import base64, re
from pathlib import Path

DATA_URI_RE = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$")

async def decode_attachments(attachments, folder: Path, client):
    files = []
    for a in attachments:
        match = DATA_URI_RE.match(a["url"])
        file_path = folder / a["name"]
        if match:
            data = base64.b64decode(match.group("data"))
            file_path.write_bytes(data)
        else:
            try:
                r = await client.get(a["url"], timeout=20)
                r.raise_for_status()
                file_path.write_bytes(r.content)
            except Exception:
                continue
        files.append(a["name"])
    return files
