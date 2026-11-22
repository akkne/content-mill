from uuid import UUID

from app.domain.knowledge import KnowledgeNode
from app.domain.video import InvalidVideo, VideoSource


def cast_options(nodes: list[KnowledgeNode]):
    return {
        "avatars": [
            {"id": n.id, "name": n.name, "default_voice_id": n.linked_voice_id}
            for n in nodes
            if n.folder_role == "avatar"
        ],
        "cast_voices": [
            {
                "id": n.id,
                "name": n.name,
                "preview": n.voice_preview_url,
                "external_id": n.elevenlabs_voice_id,
            }
            for n in nodes
            if n.folder_role == "voice" and n.elevenlabs_voice_id
        ],
    }


def resolve_cast(
    rows, nodes: list[KnowledgeNode], versions: list[VideoSource], selected: list[UUID]
):
    by_id = {node.id: node for node in nodes}
    selected_ids = set(selected)
    latest = {}
    chosen = {}
    for version in versions:
        if version.id in selected_ids:
            chosen.setdefault(version.node_id, []).append(version)
        if (
            version.node_id not in latest
            or version.version > latest[version.node_id].version
        ):
            latest[version.node_id] = version
    cast, files, names = [], set(), set()
    for row in rows:
        avatar = by_id.get(row["character_id"])
        if (
            not avatar
            or avatar.folder_role != "avatar"
            or avatar.name.casefold() in names
        ):
            raise InvalidVideo(
                "Выберите разных персонажей проекта с уникальными именами."
            )
        names.add(avatar.name.casefold())
        voice = by_id.get(row["voice_id"])
        if row["voice_id"] and (
            not voice or voice.folder_role != "voice" or not voice.elevenlabs_voice_id
        ):
            raise InvalidVideo("Выберите голос, назначенный этому проекту.")
        assets = []
        for node_id, version in latest.items():
            path = []
            node = by_id[node_id]
            while node and node.id != avatar.id:
                path.append(node)
                node = by_id.get(node.parent_id)
            if not node or not path or any(n.folder_role == "consent" for n in path):
                continue
            part = path[-1]
            role = {
                "photos": {
                    "Лицо крупным планом": "face_reference",
                    "В полный рост": "full_body_reference",
                }.get(part.name, "angle_reference"),
                "wardrobe": "outfit_reference",
            }.get(
                part.folder_role,
                "character_description"
                if version.format in ("markdown", "plain")
                else "attachment",
            )
            for pinned in chosen.get(node_id, [version]):
                assets.append(
                    {
                        "version_id": str(pinned.id),
                        "role": role,
                        "path": "/".join(n.name for n in reversed(path)),
                        "selected": pinned.id in selected_ids,
                    }
                )
                files.add(pinned.id)
        cast.append(
            {
                "character_id": str(avatar.id),
                "display_name": avatar.name,
                "files": assets,
                "voice": {
                    "project_voice_id": str(voice.id),
                    "elevenlabs_voice_id": voice.elevenlabs_voice_id,
                    "model_id": voice.voice_model or "eleven_multilingual_v2",
                    "name": voice.name,
                }
                if voice
                else None,
            }
        )
    return cast, list(dict.fromkeys([*selected, *sorted(files)]))


def validate_cast_scene(shot, characters):
    people = {p["character_id"]: p for p in characters}
    visible = {str(i) for i in shot.visible_character_ids}
    if not visible.issubset(people):
        raise InvalidVideo("Unknown visible character")
    selected = {str(i) for i in shot.reference_ids}
    for character in visible:
        photos = {
            f["version_id"]
            for f in people[character]["files"]
            if f["role"] in ("face_reference", "full_body_reference", "angle_reference")
        }
        if not photos.intersection(selected):
            raise InvalidVideo("Visible character needs a photographic reference")
    last = 0
    for line in shot.utterances:
        speaker = people.get(str(line.character_id))
        if (
            not speaker
            or not speaker["voice"]
            or speaker["display_name"] != line.speaker
        ):
            raise InvalidVideo("Unknown speaker or missing assigned voice")
        if line.delivery == "on_screen" and visible != {str(line.character_id)}:
            raise InvalidVideo("Lip-sync needs a single visible speaker")
        if line.start_ms < last:
            raise InvalidVideo("Character lines overlap")
        last = line.end_ms
