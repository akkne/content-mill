from dataclasses import asdict
from uuid import UUID

from app.domain.knowledge import KnowledgeNode
from app.domain.video import InvalidVideo, VideoSource
from app.domain.voice import DEFAULT_DELIVERY, VoiceDelivery


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


def media_role(folder: str) -> str:
    return {
        "Лицо крупным планом": "face_reference",
        "В полный рост": "full_body_reference",
        "Одежда": "outfit_reference",
    }.get(folder, "angle_reference")


def resolve_cast(
    rows,
    nodes: list[KnowledgeNode],
    versions: list[VideoSource],
    deliveries: dict[UUID, VoiceDelivery],
):
    by_id = {node.id: node for node in nodes}
    cast, names = [], set()
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
        for version in versions:
            path = []
            node = by_id.get(version.node_id)
            while node and node.id != avatar.id:
                path.append(node)
                node = by_id.get(node.parent_id)
            if not node or not path or any(n.folder_role == "consent" for n in path):
                continue
            part = path[-1]
            role = (
                media_role(part.name)
                if version.format.startswith(("image/", "video/"))
                else "character_description"
                if version.format in ("markdown", "plain")
                else "attachment"
            )
            assets.append(
                {
                    "version_id": str(version.id),
                    "role": role,
                    "path": "/".join(n.name for n in reversed(path)),
                    "selected": True,
                }
            )
        cast.append(
            {
                "character_id": str(avatar.id),
                "display_name": avatar.name,
                "files": assets,
                "voice": {
                    **asdict(deliveries.get(voice.id, DEFAULT_DELIVERY)),
                    "project_voice_id": str(voice.id),
                    "elevenlabs_voice_id": voice.elevenlabs_voice_id,
                    "model_id": voice.voice_model or "eleven_multilingual_v2",
                    "name": voice.name,
                }
                if voice
                else None,
            }
        )
    return cast


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
        if photos and not photos.intersection(selected):
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


def avatar_references(work, project, characters):
    """Resolve supplementary media through current project assignments, never bucket-wide."""
    if not characters:
        return []
    nodes = work.knowledge.list(project)
    members = {UUID(c["character_id"]): c for c in characters}
    linked = {
        n.library_avatar_id: members[n.id]
        for n in nodes
        if n.id in members and n.folder_role == "avatar" and n.library_avatar_id
    }
    scopes = [(project, nodes, members)]
    library = work.videos.avatar_library(project) if linked else None
    if library:
        scopes.append((library, work.knowledge.list(library), linked))
    seen = {
        (c["character_id"], f["path"])
        for c in characters
        for f in c["files"]
        if "path" in f
    }
    references = []
    for workspace, tree, avatars in scopes:
        by_id = {n.id: n for n in tree}
        visited = set()
        for version in work.videos.sources(workspace):
            if version.node_id in visited:
                continue
            visited.add(version.node_id)
            if not version.format.startswith(("image/", "video/")):
                continue
            path = []
            node = by_id.get(version.node_id)
            while node and node.id not in avatars and node.folder_role != "consent":
                path.append(node.name)
                node = by_id.get(node.parent_id)
            if not node or node.id not in avatars or node.folder_role != "avatar":
                continue
            character = avatars[node.id]["character_id"]
            relative = "/".join(reversed(path))
            if (character, relative) in seen:
                continue
            seen.add((character, relative))
            references.append(
                {
                    "id": str(version.id),
                    "name": version.name,
                    "format": version.format,
                    "workspace": str(workspace),
                    "character_id": character,
                    "path": relative,
                    "role": media_role(path[-1]),
                }
            )
    return references
