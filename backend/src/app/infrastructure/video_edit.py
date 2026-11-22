import base64
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from app.application.video_production import Timeline


def ffmpeg(directory: Path, args: list[str]) -> bytes:
    return subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-loglevel",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            *args,
        ],
        cwd=directory,
        capture_output=True,
        check=True,
        timeout=180,
    ).stdout


def track_info(path: Path) -> tuple[dict, float]:
    info = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-f",
            "mov",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        timeout=20,
    )
    metadata = json.loads(info.stdout)
    tracks = {s["codec_type"]: s for s in metadata["streams"]}
    return tracks, float(metadata["format"].get("start_time", 0))


class FFmpegEditor:
    def inspect(self, clip: bytes) -> tuple[int, str]:
        with TemporaryDirectory(prefix="cm-scene-") as tmp:
            directory = Path(tmp)
            path = directory / "scene.mp4"
            path.write_bytes(clip)
            try:
                tracks, origin = track_info(path)
            except subprocess.CalledProcessError as error:
                raise ValueError("Undecodable MP4") from error
            length = min(
                float(tracks[k].get("start_time", origin))
                + float(tracks[k]["duration"])
                - origin
                for k in ("audio", "video")
            )
            if not 0 < length <= 10:
                raise ValueError("Unexpected clip duration")
            try:
                sheet = ffmpeg(
                    directory,
                    [
                        "-f",
                        "mov",
                        "-i",
                        path.name,
                        "-vf",
                        "fps=1,scale=140:-2,tile=4x2",
                        "-frames:v",
                        "1",
                        "-c:v",
                        "mjpeg",
                        "-f",
                        "image2pipe",
                        "pipe:1",
                    ],
                )
            except subprocess.CalledProcessError as error:
                raise ValueError("Undecodable video track") from error
            if not sheet:
                raise ValueError("No decoded frames")
            return round(length * 1000), base64.b64encode(sheet).decode()

    def render(
        self,
        clips: list[bytes],
        timeline: Timeline,
        duration: int,
        music: tuple[str, bytes] | None = None,
    ) -> bytes:
        with TemporaryDirectory(prefix="cm-render-") as tmp:
            directory = Path(tmp)
            inputs = []
            filters = []
            labels = []
            elapsed_ms = 0
            for i, cut in enumerate(timeline.cuts):
                source = directory / f"source-{i}.mp4"
                source.write_bytes(clips[cut.scene - 1])
                first, last = cut.frame_range(elapsed_ms)
                elapsed_ms += cut.end_ms - cut.start_ms
                inputs.extend(["-f", "mov", "-i", source.name])
                filters.extend(
                    [
                        f"[{i}:v]fps=24:start_time=0,trim=start_frame={first}:end_frame={last},setpts=PTS-STARTPTS,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]",
                        f"[{i}:a]aresample=48000:async=1:first_pts=0,atrim=start_sample={first * 2000}:end_sample={last * 2000},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo,apad,atrim=end_sample={(last - first) * 2000}[a{i}]",
                    ]
                )
                labels.append(f"[v{i}][a{i}]")
            filters.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=1[v][a]")
            video_label, audio_label = "[v]", "[a]"
            if timeline.subtitles:

                def stamp(ms):
                    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"

                subtitle_file = directory / "captions.srt"
                subtitle_file.write_text(
                    "\n\n".join(
                        f"{i}\n{stamp(s.start_ms)} --> {stamp(s.end_ms)}\n{s.text}"
                        for i, s in enumerate(timeline.subtitles, 1)
                    ),
                    encoding="utf-8",
                )
                filters.append("[v]subtitles=captions.srt[vsub]")
                video_label = "[vsub]"
            if music and timeline.music:
                fmt, body = music
                (directory / "music").write_bytes(body)
                demuxer = {"audio/mp4": "mov", "audio/wav": "wav", "audio/mpeg": "mp3"}[
                    fmt
                ]
                inputs.extend(
                    [
                        "-ss",
                        str(timeline.music.start_ms / 1000),
                        "-f",
                        demuxer,
                        "-i",
                        "music",
                    ]
                )
                filters.extend(
                    [
                        f"[{len(labels)}:a]aresample=48000,volume={timeline.music.gain_db}dB,afade=t=out:st={duration - 1}:d=1[bg]",
                        "[a][bg]amix=inputs=2:duration=first:normalize=0,alimiter=latency=1[mix]",
                    ]
                )
                audio_label = "[mix]"
            ffmpeg(
                directory,
                [
                    *inputs,
                    "-filter_complex",
                    ";".join(filters),
                    "-map",
                    video_label,
                    "-map",
                    audio_label,
                    "-c:v",
                    "libx264",
                    "-r",
                    "24",
                    "-fps_mode",
                    "cfr",
                    "-preset",
                    "veryfast",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-movflags",
                    "+faststart",
                    "final.mp4",
                ],
            )
            final = directory / "final.mp4"
            tracks, _ = track_info(final)
            if any(
                abs(float(tracks[k]["duration"]) - duration) > 1 / 24
                for k in ("audio", "video")
            ):
                raise ValueError("Final track duration mismatch")
            return final.read_bytes()
