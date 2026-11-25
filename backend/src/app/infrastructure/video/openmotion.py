"""Transfer pinned media into a native OpenMotion template and export its revision."""

import json
import mimetypes
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from app.application.videos.production import ProductionError, Timeline
from app.domain.motion import DEFAULT_STYLE, STYLES
from app.infrastructure.video.video_edit import ffmpeg, track_info


def clip_tag(kind, name, src, start, length, track, extra=""):
    return (
        f'<{kind} id="{name}" class="clip" data-start="{start / 1000:g}" '
        f'data-duration="{length / 1000:g}" data-track-index="{track}" '
        f'src="{escape(src, quote=True)}" {extra}></{kind}>'
    )


def composition(
    style,
    title,
    layout,
    timeline,
    duration,
    paths,
    source,
    reel_format=None,
    insert=True,
    outro=None,
):
    """Reuse the guide's actual renderer, palette and keyframes."""
    w, h = source["width"], source["height"]
    guide_seconds = source["durationSeconds"]
    seconds = min(duration, guide_seconds)
    if layout == "split":
        seconds = duration
    if layout == "intro":
        seconds = min(seconds, 4)
    start = 0
    if reel_format:
        start = 0 if layout == "intro" else round(duration * 0.4, 3)
        seconds = min(guide_seconds, 3, duration - start)
    layers = []
    elapsed = 0
    for index, cut in enumerate(timeline.cuts):
        length = cut.end_ms - cut.start_ms
        scene = f"scene-{cut.scene}"
        offset = f'data-media-start="{cut.start_ms / 1000:g}"'
        layers.append(
            clip_tag(
                "video",
                f"shot-{index}",
                paths[scene],
                elapsed,
                length,
                0,
                offset + " muted playsinline",
            )
        )
        if scene + "-audio" in paths:
            layers.append(
                clip_tag(
                    "audio",
                    f"voice-{index}",
                    paths[scene + "-audio"],
                    elapsed,
                    length,
                    1,
                    offset,
                )
            )
        elapsed += length
    if timeline.music:
        cue = timeline.music
        layers.append(
            clip_tag(
                "audio",
                "music",
                paths["music"],
                0,
                duration * 1000,
                2,
                f'data-volume="{10 ** (cue.gain_db / 20):.5f}" data-media-start="{cue.start_ms / 1000:g}"',
            )
        )
    if timeline.photo_cutaway:
        cue = timeline.photo_cutaway
        layers.append(
            clip_tag(
                "img",
                "product",
                paths["product"],
                cue.start_ms,
                cue.end_ms - cue.start_ms,
                3,
            )
        )
    for i, card in enumerate(timeline.photo_cards):
        layers.append(
            clip_tag(
                "img",
                f"photo-{i}",
                paths[str(card.version_id)],
                card.start_ms,
                card.end_ms - card.start_ms,
                4,
            )
        )
    if insert:
        layers.append(
            f'<div class="clip" id="guide" data-composition-id="guide" data-start="{start}" data-duration="{seconds}" data-track-index="5" data-width="{w}" data-height="{h}"><canvas width="{w}" height="{h}"></canvas></div>'
        )
    for i, cue in enumerate(timeline.subtitles):
        layers.append(
            f'<div class="clip caption" id="caption-{i}" data-start="{cue.start_ms / 1000:g}" data-duration="{(cue.end_ms - cue.start_ms) / 1000:g}" data-track-index="6">{escape(cue.text)}</div>'
        )
    for i, graphic in enumerate(timeline.graphics):
        for j, beat in enumerate(graphic.beats):
            end = (
                graphic.beats[j + 1].at_ms
                if j + 1 < len(graphic.beats)
                else graphic.end_ms
            )
            layers.append(
                f'<div class="clip fact" id="fact-{i}-{j}" data-start="{beat.at_ms / 1000:g}" data-duration="{(end - beat.at_ms) / 1000:g}" data-track-index="{7 + i}">{escape(beat.label)}</div>'
            )
    outro_timeline = ""
    if outro:
        length = min(3, duration, outro["duration"])
        layers.append(
            f'<div class="clip" id="outro" data-composition-id="outro" data-start="{duration - length}" data-duration="{length}" data-track-index="16" data-width="1000" data-height="600"><canvas width="1000" height="600"></canvas></div>'
        )
        outro_timeline = f',outro:gsap.timeline({{paused:true}}).to(endClock,{{time:{length},duration:{length},ease:"none",onUpdate:()=>window.outroDemo.renderAt(endClock.time)}},0)'
    guide_scripts = (
        '<script src="demos/data.js"></script><script src="demos/common.js"></script><script src="demos/scene.js"></script>'
        if insert
        else ""
    )
    params = json.dumps(
        {"title": title[:60], "accent": style["accent"]}, ensure_ascii=False
    ).replace("<", "\\u003c")
    guide_timeline = (
        f',guide:gsap.timeline({{paused:true}}).to(clock,{{time:{seconds},duration:{seconds},ease:"none",onUpdate:draw}},0)'
        if insert
        else ""
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}body{{margin:0;background:#17191e;color:white;font:700 44px/1.12 Arial,sans-serif}}
main{{width:720px;height:1280px;position:relative;overflow:hidden}}video,img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
#outro{{position:absolute;left:5%;width:90%;height:32%;top:47%;overflow:hidden;border-radius:22px}}
#guide{{position:absolute;left:5%;width:90%;top:54%;height:32%;overflow:hidden;border-radius:22px}}
canvas{{width:100%;height:100%;object-fit:contain}}
.split video{{height:56%}}.split #guide{{left:0;top:56%;height:44%;width:100%;border-radius:0}}
.intro #guide{{inset:0;width:100%;height:100%;background:#17191e;border-radius:0}}
.caption,.fact{{position:absolute;text-align:center;left:6%;right:6%;bottom:7%;text-shadow:0 2px 9px black;background:#13151cce;border-radius:10px;padding:8px}}
.fact{{bottom:auto;top:8%;font-size:50px;color:{style["accent"]}}}
.reel-story .caption{{left:8%;right:8%;bottom:11%;background:#111b24da;border-radius:0;border-left:6px solid #e7bc76;padding:16px 20px;text-align:left;font-family:Georgia,serif}}
.reel-steps .caption{{left:7%;right:7%;bottom:11%;text-align:left;background:#f8efda;color:#162b31;text-shadow:none;border-radius:16px;padding:18px 24px;border-top:8px solid #ef744b}}
.reel-pulse .caption{{bottom:13%;background:#e9fb55;color:#151515;text-transform:uppercase;font-weight:900;text-shadow:none;border-radius:2px;transform:rotate(-2deg)}}
</style></head><body data-mode="sequence"><main class="{layout if insert else ""} {reel_format or ""}" data-composition-id="main" data-start="0" data-duration="{duration}" data-width="720" data-height="1280" data-fps="24">
{"".join(layers)}</main><script src="assets/gsap.min.js"></script>{guide_scripts}{'<script src="demos/cm-outro.js"></script>' if outro else ""}
<script>const clock={{time:0}},endClock={{time:0}};const draw=()=>{{window.motionDemo.setParams({params});window.motionDemo.renderAt(clock.time % ({guide_seconds}+0.001))}};
window.__timelines={{main:gsap.timeline({{paused:true}}){guide_timeline}{outro_timeline}}};
{f'window.__timelines.main.set("video",{{height:"100%"}},0).set("video",{{height:"56%"}},{start}).set("video",{{height:"100%"}},{start + seconds});' if insert and reel_format and layout == "split" else ""}
{"draw();" if insert else ""}</script></body></html>"""


class OpenMotion:
    def __init__(self, url: str, inbox: Path = Path("/motion-inbox")):
        self.url = url.rstrip("/")
        self.inbox = inbox

    def call(self, name, **arguments):
        # Studio accepts loopback Host / Origin; the Compose network is private.
        origin = "http://127.0.0.1:" + str(urlsplit(self.url).port or 4173)
        r = httpx.post(
            self.url + "/motion-api/phase1/call",
            headers={"Host": urlsplit(origin).netloc, "Origin": origin},
            json={"name": "openmotion_" + name, "arguments": arguments},
            timeout=180,
        )
        r.raise_for_status()
        return r.json()

    def submit(
        self,
        video_id: UUID,
        title,
        template,
        layout,
        clips,
        timeline: Timeline,
        duration,
        music,
        photo,
        cards,
        reel_format=None,
        outro_template=None,
    ):
        style = STYLES[template or DEFAULT_STYLE]
        key = "cm-" + str(video_id)
        project = self.call(
            "create_project",
            requestId=key,
            projectType="template",
            templateId=style["id"],
            title=title[:60],
            requirements="Content Mill · " + title,
            guideDraft={"title": title[:60], "accent": style["accent"]},
        )
        pid = project["projectId"]
        folder = self.inbox / key
        folder.mkdir(parents=True, exist_ok=True)
        files = {}

        def add(name, extension, data):
            path = folder / (name + extension)
            path.write_bytes(data)
            files[name] = path

        try:
            for i, clip in enumerate(clips, 1):
                name = f"scene-{i}"
                add(name, ".mp4", clip)
                audio = folder / (name + ".m4a")
                tracks, origin = track_info(files[name])
                if "audio" in tracks:
                    delay = max(
                        0,
                        round(
                            1000
                            * (
                                float(tracks["audio"].get("start_time", origin))
                                - origin
                            )
                        ),
                    )
                    ffmpeg(
                        folder,
                        [
                            "-y",
                            "-f",
                            "mov",
                            "-i",
                            files[name].name,
                            "-vn",
                            "-af",
                            f"adelay={delay}:all=1",
                            "-c:a",
                            "aac",
                            audio.name,
                        ],
                    )
                    files[name + "-audio"] = audio
            if music:
                add("music", mimetypes.guess_extension(music[0]) or ".mp3", music[1])
            for name, data in ([("product", photo)] if photo else []) + list(
                cards.items()
            ):
                ext = (
                    ".png"
                    if data.startswith(b"\x89PNG")
                    else ".webp"
                    if data.startswith(b"RIFF")
                    else ".jpg"
                )
                add(str(name), ext, data)
            result = self.call(
                "import_assets",
                projectId=pid,
                requestId=key + "-media",
                items=[
                    {"itemId": n, "sourcePath": str(p), "name": p.name}
                    for n, p in files.items()
                ],
            )
            if result["status"] != "completed":
                raise ValueError("OpenMotion asset import failed")
            paths = {i["itemId"]: i["path"] for i in result["items"]}
        finally:
            shutil.rmtree(folder, ignore_errors=True)
        outro = STYLES.get(outro_template)
        files_to_edit = []
        if outro:
            files_to_edit.append(
                {
                    "path": "demos/cm-outro.js",
                    "content": self.outro_script(outro, title),
                }
            )
        html = composition(
            style,
            title,
            layout,
            timeline,
            duration,
            paths,
            project["source"],
            reel_format,
            bool(template),
            outro,
        )
        rev = result["version"]
        saved = self.call(
            "edit_project",
            projectId=pid,
            requestId=key + "-edit",
            expectedRevision=rev["revision"],
            expectedVersionId=rev["versionId"],
            files=[*files_to_edit, {"path": "index.html", "content": html}],
        )
        audio = (
            "required"
            if any(k.endswith("-audio") or k == "music" for k in paths)
            else "optional"
        )
        job = self.call(
            "export_request",
            projectId=pid,
            requestId=key + "-export",
            expectedRevision=saved["revision"],
            versionId=saved["version"]["versionId"],
            audio=audio,
        )
        return {
            "project": pid,
            "job": job["job"]["id"],
            "version": saved["version"]["versionId"],
            "revision": saved["revision"],
            "audio": audio,
        }

    def outro_script(self, style, title):
        """Keep the second guide's drawing state and canvas separate from the first."""
        base = f"{self.url}/api/template-source/{style['id']}/demos/"
        scripts = []
        with httpx.Client(timeout=30) as client:
            for name in ("data.js", "common.js", "scene.js"):
                response = client.get(
                    base + name,
                    headers={
                        "Host": "127.0.0.1:" + str(urlsplit(self.url).port or 4173)
                    },
                )
                response.raise_for_status()
                scripts.append(response.text)
        params = json.dumps({"title": title[:60], "accent": style["accent"]})
        return "\n".join(
            [
                "(()=>{const window={};const document={body:globalThis.document.body,querySelector:s=>globalThis.document.querySelector('#outro '+s),createElement:s=>globalThis.document.createElement(s)};",
                *scripts,
                f"globalThis.outroDemo=window.motionDemo;globalThis.outroDemo.setParams({params});}})();",
            ]
        )

    def retry(self, receipt):
        result = self.call(
            "export_request",
            projectId=receipt["project"],
            requestId="retry-" + receipt["job"],
            versionId=receipt["version"],
            expectedRevision=receipt["revision"],
            audio=receipt["audio"],
        )
        return {**receipt, "job": result["job"]["id"]}

    def collect(self, receipt):
        job = self.call(
            "get_project", projectId=receipt["project"], exportJobId=receipt["job"]
        )["exportJob"]
        if job["state"] in ("failed", "cancelled"):
            raise ProductionError("render_failed", terminal=True)
        if job["state"] != "completed":
            return None
        if job["verification"]["status"] != "passed":
            raise ValueError("OpenMotion export failed verification")
        url = urlsplit(job["downloadUrl"])
        r = httpx.get(
            self.url + url.path + ("?" + url.query if url.query else ""),
            headers={"Host": url.netloc},
            timeout=120,
        )
        r.raise_for_status()
        return r.content
