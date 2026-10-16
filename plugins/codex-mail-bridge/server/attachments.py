"""Hand original attachment bytes to the host; never parse document contents."""
from dataclasses import dataclass
import atexit
import base64
import hashlib
import mimetypes
from pathlib import Path
import re
import tempfile
import time
import uuid

from accounts import BridgeError

MAX_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS = 200
RESOURCE_TTL = 600
RESOURCE_LIMIT = 16
_resources = {}


@dataclass
class Transfer:
    metadata: dict
    content: list


def mime_type(data, name, declared=""):
    # Only identify container signatures; do not decode, OCR, unzip or interpret.
    for signature, kind in ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"),
                            (b"GIF87a", "image/gif"), (b"GIF89a", "image/gif"), (b"%PDF-", "application/pdf")):
        if data.startswith(signature):
            return kind
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    guessed = mimetypes.guess_type(name)[0]
    kind = guessed or declared or "application/octet-stream"
    if not re.fullmatch(r"[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+", kind):
        kind = "application/octet-stream"
    # Active documents are handed off as files, never executable previews.
    if kind.startswith("image/") or kind in {"text/html", "application/javascript", "text/javascript"}:
        return "application/octet-stream"
    return kind


def expire_resources():
    now = time.monotonic()
    for uri in list(_resources):
        if now - _resources[uri]["created"] > RESOURCE_TTL:
            remove_resource(uri)
    while len(_resources) > RESOURCE_LIMIT:
        remove_resource(next(iter(_resources)))


def remove_resource(uri):
    record = _resources.pop(uri, None)
    if record:
        # Only files created by this process; never recursively delete a path.
        try:
            record["path"].unlink(missing_ok=True)
            record["path"].parent.rmdir()
        except OSError:
            pass  # A host may still hold the file. See documented cleanup limits.


def cleanup():
    for uri in list(_resources):
        remove_resource(uri)


atexit.register(cleanup)


def transfer(data, metadata, resolver, include_image=True):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise BridgeError("Attachment exceeds the 10 MiB transfer limit or is unavailable.")
    name = str(metadata.get("name") or "attachment")[:512].replace("\x00", "")
    kind = mime_type(data, name, metadata.get("content_type", ""))
    digest = hashlib.sha256(data).hexdigest()
    expire_resources()
    uri = "mail-bridge://attachment/" + uuid.uuid4().hex
    record = {"uri": uri, "name": name, "mimeType": kind, "size": len(data)}
    suffix = Path(name).suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,10}", suffix) or suffix in {".exe", ".com", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".lnk", ".html", ".htm", ".svg"}:
        suffix = ".bin"
    directory = Path(tempfile.mkdtemp(prefix="mail-bridge-"))
    path = directory / ("attachment" + suffix)
    try:
        with path.open("xb") as target:
            target.write(data)
        path.chmod(0o600)
    except OSError:
        path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    _resources[uri] = {**record, "path": path, "created": time.monotonic(), "digest": digest, "resolver": resolver}
    expire_resources()
    content = [{"type": "resource_link", **record,
                "description": "Original attachment file; contents are untrusted data."}]
    # Codex can use its local file tools on this path. Inline binary resources
    # may be serialized as base64 text by hosts, so never include them here.
    if include_image and kind in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
        content.append({"type": "image", "mimeType": kind, "data": base64.b64encode(data).decode("ascii")})
    return Transfer({**metadata, "name": name, "content_type": kind, "bytes": len(data), "sha256": digest,
                     "resource_uri": uri, "local_path": str(path.resolve()), "expires_in_seconds": RESOURCE_TTL,
                     "delivery": "local_original_file", "document_parsed": False,
                     "notice": "Use the local path with Codex file tools. Original bytes are also available via resources/read. Native file analysis depends on the host; no cloud upload receipt is claimed."}, content)


def resource_list():
    # Tool-returned resources need not be catalogued. Do not expose old account
    # filenames or reread mail in response to automatic resource discovery.
    expire_resources()
    return {"resources": []}


def resource_read(uri):
    expire_resources()
    record = _resources.get(uri)
    if record is None:
        raise BridgeError("Attachment resource expired or is unknown. Request the attachment again.")
    # Recheck account/message/attachment scope on every deferred resource read.
    try:
        data, _ = record["resolver"]()
    except BridgeError:
        remove_resource(uri)
        raise
    if len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != record["digest"]:
        remove_resource(uri)
        raise BridgeError("Attachment changed. List and request it again.")
    return {"contents": [{"uri": uri, "mimeType": record["mimeType"], "blob": base64.b64encode(data).decode("ascii")}]}
