"""Keep selected original files available between one-shot local CLI calls."""
from dataclasses import dataclass
import hashlib
import mimetypes
import os
from pathlib import Path
import re
import stat
import time
import uuid

from accounts import BridgeError, settings_path

MAX_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS = 200
EXPORT_TTL = 600
EXPORT_LIMIT = 16
TOKEN = re.compile(r"e_[0-9a-f]{32}")
SAFE_FILE = re.compile(r"attachment\.[a-z0-9]{1,10}")


@dataclass
class Transfer:
    metadata: dict


def mime_type(data, name, declared=""):
    # Identify signatures only; never decode, OCR, unzip or interpret documents.
    for signature, kind in ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"),
                            (b"GIF87a", "image/gif"), (b"GIF89a", "image/gif"), (b"%PDF-", "application/pdf")):
        if data.startswith(signature):
            return kind
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    kind = mimetypes.guess_type(name)[0] or declared or "application/octet-stream"
    if not re.fullmatch(r"[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+", kind):
        kind = "application/octet-stream"
    if kind.startswith("image/") or kind in {"text/html", "application/javascript", "text/javascript"}:
        return "application/octet-stream"
    return kind


def is_link(path):
    # Windows junctions/reparse points must not redirect export cleanup.
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def export_root(create=False):
    configured = os.environ.get("MAIL_BRIDGE_EXPORT_ROOT")
    root = Path(configured).expanduser() if configured else settings_path().parent / "exports"
    if root.exists() or root.is_symlink():
        if is_link(root) or not root.is_dir():
            raise BridgeError("Unsafe attachment export directory.", code="export_unavailable")
    elif create:
        root.mkdir(parents=True, mode=0o700)
        root.chmod(0o700)
    return root


def managed_exports():
    root = export_root()
    if not root.exists():
        return []
    found = []
    for directory in root.iterdir():
        if not TOKEN.fullmatch(directory.name) or is_link(directory) or not directory.is_dir():
            continue
        files = list(directory.iterdir())
        if len(files) == 1 and SAFE_FILE.fullmatch(files[0].name) and not is_link(files[0]) and files[0].is_file():
            found.append((files[0].stat().st_mtime, directory, files[0]))
    return sorted(found, key=lambda item: (item[0], item[1].name))


def remove_export(directory, path):
    # Only a generated file and its empty directory; never recursive deletion.
    try:
        if is_link(directory) or is_link(path):
            return False
        path.unlink()
        directory.rmdir()
        return True
    except OSError:
        return False


def expire_exports(reserve=0):
    found = managed_exports()
    now = time.time()
    removed = 0
    remaining = len(found)
    for created, directory, path in found:
        if now - created > EXPORT_TTL or remaining > EXPORT_LIMIT - reserve:
            if remove_export(directory, path):
                removed += 1
                remaining -= 1
    if remaining > EXPORT_LIMIT - reserve:
        raise BridgeError("Attachment export limit reached; a file may be locked.",
                          code="export_limit", next_action="release_finished_exports")
    return {"removed": removed, "remaining": remaining}


def release_export(export_id):
    if not isinstance(export_id, str) or not TOKEN.fullmatch(export_id):
        raise BridgeError("Invalid export ID.", code="invalid_arguments")
    for _, directory, path in managed_exports():
        if directory.name == export_id:
            if not remove_export(directory, path):
                raise BridgeError("Export could not be removed; close any file handle and retry.", code="export_locked", retryable=True)
            return {"released": True}
    return {"released": False}


def cleanup():
    """Explicitly clear managed exports; used only in isolated tests."""
    for _, directory, path in managed_exports():
        remove_export(directory, path)


def transfer(data, metadata):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise BridgeError("Attachment exceeds the 10 MiB transfer limit or is unavailable.", code="attachment_unavailable")
    name = str(metadata.get("name") or "attachment")[:512].replace("\x00", "")
    kind = mime_type(data, name, metadata.get("content_type", ""))
    suffix = Path(name).suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,10}", suffix) or suffix in {".exe", ".com", ".bat", ".cmd", ".ps1", ".js", ".vbs", ".lnk", ".html", ".htm", ".svg"}:
        suffix = ".bin"
    root = export_root(create=True)
    expire_exports(reserve=1)
    export_id = "e_" + uuid.uuid4().hex
    directory = root / export_id
    directory.mkdir(mode=0o700)
    path = directory / ("attachment" + suffix)
    try:
        with path.open("xb") as target:
            target.write(data)
        path.chmod(0o600)
    except OSError:
        path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    return Transfer({**metadata, "name": name, "content_type": kind, "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(), "export_id": export_id,
                     "local_path": str(path.resolve()), "expires_in_seconds": EXPORT_TTL,
                     "delivery": "local_original_file", "document_parsed": False,
                     "notice": "Use authorized host file tools on local_path. Image viewing is a separate explicit host action. Release export_id after use. No cloud upload or file analysis is claimed."})
