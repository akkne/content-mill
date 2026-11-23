import base64
import json
import math
import subprocess
import wave
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from PIL import Image, ImageDraw, ImageOps

from app.application.videos.production import ProductionError, Timeline
from app.domain.video import DEFAULT_EDITING_STYLE, FACTS_STYLE, STORY_STYLE
from app.infrastructure.video.asset_preview import check_size
from app.infrastructure.video.editorial_graphic import graphic_frame
from app.infrastructure.video.reference_captions import reference_captions


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
            if not 0 < length <= 10 + 1 / 24:
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
                        "fps=1,scale=140:-2,tile=5x2",
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
        product_photo: bytes | None = None,
        editing_style: str = DEFAULT_EDITING_STYLE,
        card_images: dict[UUID, bytes] | None = None,
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
                motion = ""
                if cut.push_in:
                    frames = max(1, last - first - 1)
                    motion = (
                        f",scale=1440:2560,zoompan=z='1+0.09*on/{frames}'"
                        ":x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=720x1280:fps=24"
                    )
                filters.extend(
                    [
                        f"[{i}:v]fps=24:start_time=0,trim=start_frame={first}:end_frame={last},setpts=PTS-STARTPTS,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1{motion}[v{i}]",
                        f"[{i}:a]aresample=48000:async=1:first_pts=0,atrim=start_sample={first * 2000}:end_sample={last * 2000},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo,apad,atrim=end_sample={(last - first) * 2000}[a{i}]",
                    ]
                )
                labels.append(f"[v{i}][a{i}]")
            filters.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=1[v][a]")
            video_label, audio_label = "[v]", "[a]"
            insert = timeline.photo_cutaway
            if insert:
                if not product_photo:
                    raise ValueError("Missing product photo")
                with Image.open(
                    BytesIO(product_photo), formats=["PNG", "JPEG", "WEBP"]
                ) as original:
                    check_size(*original.size)
                    picture = ImageOps.exif_transpose(original).convert("RGBA")
                    bounds = (648, 890) if editing_style == STORY_STYLE else (720, 1280)
                    picture = ImageOps.contain(
                        picture, bounds, Image.Resampling.LANCZOS
                    )
                    canvas = Image.new("RGB", (720, 1280), "#101010")
                    canvas.paste(
                        picture,
                        ((720 - picture.width) // 2, (1280 - picture.height) // 2),
                        picture,
                    )
                    canvas.save(directory / "product.png")
                inputs.extend(["-f", "image2", "-i", "product.png"])
                filters.append(
                    f"[v][{len(labels)}:v]overlay=enable='gte(t,{insert.start_ms / 1000})*lt(t,{insert.end_ms / 1000})'[withphoto]"
                )
                video_label = "[withphoto]"
            next_input = len(labels) + int(insert is not None)
            for index, card in enumerate(timeline.photo_cards):
                filename = f"card-{index}.png"
                with Image.open(
                    BytesIO((card_images or {})[card.version_id]),
                    formats=["PNG", "JPEG", "WEBP"],
                ) as source:
                    check_size(*source.size)
                    photo = ImageOps.contain(
                        ImageOps.exif_transpose(source).convert("RGB"),
                        (620, 790),
                        Image.Resampling.LANCZOS,
                    )
                    mask = Image.new("L", photo.size)
                    ImageDraw.Draw(mask).rounded_rectangle(
                        (0, 0, photo.width - 1, photo.height - 1), radius=18, fill=255
                    )
                    photo.putalpha(mask)
                    photo.save(directory / filename)
                start = card.start_ms / 1000
                active = f"gte(t,{start})*lt(t,{card.end_ms / 1000})"
                inputs.extend(["-f", "image2", "-i", filename])
                filters.extend(
                    [
                        f"{video_label}drawbox=w=iw:h=ih:c=0x101010:t=fill:enable='{active}'[matte{index}]",
                        f"[matte{index}][{next_input}:v]overlay=x='(W-w)/2':y='(H-h)/2-82+48*max(0,1-(t-{start})/0.22)':enable='{active}'[card{index}]",
                    ]
                )
                next_input += 1
                video_label = f"[card{index}]"
            for graphic in timeline.graphics:
                for index, beat in enumerate(graphic.beats):
                    end = (
                        graphic.beats[index + 1].at_ms
                        if index + 1 < len(graphic.beats)
                        else graphic.end_ms
                    )
                    filename = f"graphic-{next_input}.png"
                    graphic_frame(graphic, index).save(directory / filename)
                    inputs.extend(["-f", "image2", "-i", filename])
                    label = f"[graphic{next_input}]"
                    filters.append(
                        f"{video_label}[{next_input}:v]overlay=enable='gte(t,{beat.at_ms / 1000})*lt(t,{end / 1000})'{label}"
                    )
                    video_label = label
                    next_input += 1
            if timeline.subtitles and editing_style in (FACTS_STYLE, STORY_STYLE):
                (directory / "captions.ass").write_text(
                    reference_captions(timeline.subtitles, editing_style),
                    encoding="utf-8",
                )
                filters.append(f"{video_label}subtitles=captions.ass[vsub]")
                video_label = "[vsub]"
            elif timeline.subtitles:

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
                filters.append(f"{video_label}subtitles=captions.srt[vsub]")
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
                        f"[{next_input}:a]aresample=48000,volume={timeline.music.gain_db}dB,afade=t=out:st={duration - 1}:d=1[bg]",
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

    def prepare_line(self, audio: bytes, window_ms: int) -> bytes:
        with TemporaryDirectory(prefix="cm-line-") as tmp:
            directory = Path(tmp)
            (directory / "line").write_bytes(audio)
            args = ["-i", "line", "-vn", "-ac", "1", "-ar", "24000"]
            pcm = ffmpeg(directory, args + ["-f", "s16le", "pipe:1"])
            budget = window_ms * 48  # 24 samples per ms, signed 16-bit mono
            if not pcm or len(pcm) > budget * 1.35:
                raise ProductionError("speech_too_long")
            if len(pcm) > budget:
                tempo = len(pcm) / budget * 1.01
                pcm = ffmpeg(
                    directory,
                    args + ["-af", f"atempo={tempo:.8f}", "-f", "s16le", "pipe:1"],
                )
            if len(pcm) > budget:
                raise ProductionError("speech_too_long")
            return wav_bytes(pcm)

    def speech_track(
        self, lines: list[tuple[int, int, bytes]], duration_ms: int
    ) -> bytes:
        pcm = bytearray(duration_ms * 48)
        for start, end, audio in lines:
            with wave.open(BytesIO(audio), "rb") as track:
                samples = track.readframes(track.getnframes())
            if not 0 <= start < end <= duration_ms or len(samples) > (end - start) * 48:
                raise ValueError("Invalid line timing")
            offset = start * 48
            pcm[offset : offset + len(samples)] = samples
        return wav_bytes(pcm)

    def dub(self, clip: bytes, audio: bytes) -> bytes:
        with TemporaryDirectory(prefix="cm-dub-") as tmp:
            directory = Path(tmp)
            (directory / "video.mp4").write_bytes(clip)
            (directory / "speech.wav").write_bytes(audio)
            # Avatar providers can drop a few frames of trailing silence.
            # Keep the authored audio intact and hold the last picture in that gap.
            video = track_info(directory / "video.mp4")[0]["video"]
            picture_end = float(video.get("start_time", 0)) + float(video["duration"])
            # Montage trims both streams to the approved cut. Using -shortest
            # with packet-copy here can drop reordered video frames at its end.
            video_args = ["-c:v", "copy"]
            with wave.open(BytesIO(audio), "rb") as track:
                rate = track.getframerate()
                samples = track.getnframes()
                gap = samples / rate - picture_end
                if 0 < gap <= 0.25:
                    track.setpos(max(0, min(samples, math.floor(picture_end * rate))))
                    if not any(track.readframes(samples - track.tell())):
                        frames = math.ceil(samples * 24 / rate)
                        video_args = [
                            "-vf",
                            f"fps=24:start_time=0,tpad=stop_mode=clone:stop=-1,trim=end_frame={frames}",
                            "-c:v",
                            "libx264",
                            "-preset",
                            "veryfast",
                        ]
            ffmpeg(
                directory,
                [
                    "-i",
                    "video.mp4",
                    "-i",
                    "speech.wav",
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    *video_args,
                    "-c:a",
                    "aac",
                    "out.mp4",
                ],
            )
            return (directory / "out.mp4").read_bytes()


def wav_bytes(samples: bytes | bytearray) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as track:
        track.setparams((1, 2, 24000, 0, "NONE", ""))
        track.writeframes(samples)
    return output.getvalue()
