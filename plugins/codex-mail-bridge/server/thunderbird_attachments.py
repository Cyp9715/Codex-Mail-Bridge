"""Selected-account, bounded local MIME-cache access. No downloads or mail writes."""
from email import policy
from email.parser import BytesHeaderParser, BytesParser
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time
from urllib.parse import unquote, urlsplit

import attachments
from accounts import BridgeError, database, read_accounts, selection

MAX_MESSAGE = 32 * 1024 * 1024
MAX_SCAN = 64 * 1024 * 1024
MAX_HEADERS = 65536


def preferences(profile):
    values = {}
    for line in (profile["path"] / "prefs.js").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r'user_pref\("(mail\.(?:account|server)\.[^"\r\n]+)", (.+)\);', line.strip())
        if match:
            value = json.loads(match[2])
            if isinstance(value, (str, int, bool)):
                values[match[1]] = value
    return values


def storage_root(profile, account, prefs):
    server = prefs.get("mail.account." + account["id"] + ".server")
    if not isinstance(server, str):
        raise BridgeError("Selected account storage configuration is unavailable.")
    base = "mail.server." + server + "."
    relative = prefs.get(base + "directory-rel")
    absolute = prefs.get(base + "directory")
    if isinstance(relative, str) and relative.startswith("[ProfD]"):
        root = profile["path"] / relative[7:].replace("\\", "/")
    elif isinstance(absolute, str) and Path(absolute).is_absolute():
        root = Path(absolute)
    else:
        raise BridgeError("Mail cache path is not registered. No path is guessed.")
    root = root.resolve(strict=True)
    contract = prefs.get(base + "storeContractID", "@mozilla.org/msgstore/berkeleystore;1")
    if contract not in {"@mozilla.org/msgstore/berkeleystore;1", "@mozilla.org/msgstore/maildirstore;1"}:
        raise BridgeError("This Thunderbird message-store format is unsupported.")
    return root, contract


def scoped_cache_path(profile, account, folder_uri):
    prefs = preferences(profile)
    root, contract = storage_root(profile, account, prefs)
    for other in read_accounts(profile):
        if other["id"] == account["id"]:
            continue
        try:
            other_root, _ = storage_root(profile, other, prefs)
        except (BridgeError, OSError):
            continue
        if root == other_root or root.is_relative_to(other_root) or other_root.is_relative_to(root):
            raise BridgeError("Account storage directories overlap; attachment access is refused.")
    parsed = urlsplit(folder_uri)
    if parsed.query or parsed.fragment:
        raise BridgeError("Unsupported folder URI.")
    pieces = [unquote(part) for part in parsed.path.lstrip("/").split("/")]
    if not pieces or len(pieces) > 30 or any(not p or p in {".", ".."} or
            re.search(r'[\\/:<>"|?*\x00-\x1f]', p) or p.endswith((".msf", ".sbd", ".", " ")) for p in pieces):
        raise BridgeError("Cannot safely map this folder to its local cache.")
    candidate = root.joinpath(*(p + ".sbd" for p in pieces[:-1]), pieces[-1])
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise BridgeError("Folder cache escaped the selected account storage.")
    return resolved, contract


def identity(raw):
    header = raw.split(b"\n\n", 1)[0].split(b"\r\n\r\n", 1)[0]
    if len(header) > MAX_HEADERS:
        return ""
    message = BytesHeaderParser(policy=policy.default).parsebytes(header + b"\n\n")
    values = message.get_all("Message-ID", [])
    return str(values[0]).strip().strip("<>") if len(values) == 1 else ""


def read_regular(path, limit):
    with path.open("rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise BridgeError("Mail cache is not a regular file.")
        data = source.read(limit + 1)
    if len(data) > limit:
        raise BridgeError("Cached message exceeds the local transfer safety limit.")
    return data


def mbox_message(path, expected, message_key):
    with path.open("rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise BridgeError("Mail cache is not a regular file.")
        # Some Thunderbird versions use byte offsets; verify rather than assuming.
        if type(message_key) is int and 0 <= message_key < info.st_size:
            source.seek(message_key)
            if source.readline(MAX_HEADERS).startswith(b"From "):
                raw = source.read(MAX_MESSAGE + 1)
                boundary = re.search(rb"(?m)^From ", raw)
                raw = raw[:boundary.start()] if boundary else raw
                if len(raw) <= MAX_MESSAGE and identity(raw) == expected:
                    return raw
        # Bounded recent-cache fallback handles stores whose keys are not offsets.
        start = max(0, info.st_size - MAX_SCAN)
        source.seek(start)
        window = source.read(MAX_SCAN)
    starts = [m.start() for m in re.finditer(rb"(?m)^From ", window)]
    matches = []
    deadline = time.monotonic() + 5
    for n, offset in enumerate(starts):
        if time.monotonic() > deadline:
            raise BridgeError("Bounded mail-cache scan timed out. No attachment was returned.")
        end = starts[n + 1] if n + 1 < len(starts) else len(window)
        newline = window.find(b"\n", offset, end)
        raw = window[newline + 1:end] if newline >= 0 else b""
        if len(raw) <= MAX_MESSAGE and identity(raw) == expected:
            matches.append(raw)
            if len(matches) > 1:
                raise BridgeError("Ambiguous message identity in the local cache.")
    if len(matches) != 1:
        raise BridgeError("Message is not available in the bounded local MIME cache. Sync normally in Thunderbird; no network fetch is attempted.")
    return matches[0]


def maildir_message(path, expected):
    matches = []
    inspected = 0
    deadline = time.monotonic() + 5
    for name in ("cur", "new"):
        folder = path / name
        if not folder.is_dir():
            continue
        folder = folder.resolve(strict=True)
        if not folder.is_relative_to(path):
            raise BridgeError("Maildir cache escaped the selected folder.")
        for item in folder.iterdir():
            inspected += 1
            if inspected > 2000 or time.monotonic() > deadline:
                raise BridgeError("Bounded maildir scan is incomplete. No attachment was returned.")
            if item.is_symlink() or not item.is_file() or not item.resolve().is_relative_to(folder):
                continue
            with item.open("rb") as source:
                header = source.read(MAX_HEADERS)
            if identity(header) == expected:
                matches.append(read_regular(item, MAX_MESSAGE))
                if len(matches) > 1:
                    raise BridgeError("Ambiguous message identity in the local cache.")
    if len(matches) != 1:
        raise BridgeError("Message is not present in the local maildir cache.")
    return matches[0]


def selected_message(message_id):
    with database() as (db, folders, profile, account):
        columns = {r["name"] for r in db.execute("PRAGMA table_info(messages)")}
        key = "m.messageKey" if "messageKey" in columns else "NULL"
        ids = [f["id"] for f in folders]
        row = db.execute("SELECT m.headerMessageID, " + key + " AS cache_key, f.folderURI "
                         "FROM messages m JOIN folderLocations f ON f.id=m.folderID "
                         "WHERE m.id=? AND m.deleted=0 AND m.folderID IN (" + ",".join("?" for _ in ids) + ")",
                         [message_id, *ids]).fetchone()
        if row is None:
            raise BridgeError("Message is outside the selected account's indexed folders.")
        expected = str(row["headerMessageID"] or "").strip().strip("<>")
        if not expected or "\n" in expected or "\r" in expected:
            raise BridgeError("Indexed message identity is unavailable.")
        path, contract = scoped_cache_path(profile, account, row["folderURI"])
        raw = maildir_message(path, expected) if "maildirstore" in contract else mbox_message(path, expected, row["cache_key"])
        if identity(raw) != expected:
            raise BridgeError("Cached MIME does not match the selected indexed message.")
        current_profile, current_account = selection()
        if current_profile["id"] != profile["id"] or current_account["fingerprint"] != account["fingerprint"]:
            raise BridgeError("Selected account changed during attachment access.")
        return raw, {**account, "cache_scope": profile["id"] + account["fingerprint"]}


def parts(raw, account, message_id):
    message = BytesParser(policy=policy.default).parsebytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    pending = [(message, 0)]
    result = []
    visited = 0
    while pending:
        part, depth = pending.pop(0)
        visited += 1
        if depth > 30 or visited > 1000:
            raise BridgeError("MIME structure exceeds safety limits.")
        if part.defects:
            raise BridgeError("Cached MIME is incomplete or malformed; original bytes cannot be verified.")
        kind = part.get_content_type()
        if kind in {"multipart/encrypted", "application/pkcs7-mime", "application/x-pkcs7-mime"}:
            raise BridgeError("Encrypted/protected mail attachments are not transferred.")
        if kind.startswith("message/"):
            # Attached messages remain opaque files; never descend into their mail.
            continue
        if part.is_multipart():
            pending.extend((child, depth + 1) for child in part.iter_parts())
            continue
        name = part.get_filename()
        cid = str(part.get("Content-ID") or "")[:512]
        if not (name or cid or part.get_content_disposition() == "attachment" or kind.startswith("image/")):
            continue
        token = hashlib.sha256((account["cache_scope"] + ":" + str(message_id) + ":" + digest + ":" + str(visited)).encode()).hexdigest()
        meta = {"id": "a_" + token, "name": str(name or "inline-attachment")[:512], "content_type": kind,
                "bytes": None, "size_note": "Decoded byte count is checked only for the requested file.",
                "inline": bool(cid or part.get_content_disposition() == "inline"),
                "content_id": cid, "transferable": True}
        result.append((meta, part))
        if len(result) > attachments.MAX_ATTACHMENTS:
            raise BridgeError("Message contains too many attachments for one bounded listing.")
    return result


def list_attachments(message_id, limit=20, offset=0):
    raw, account = selected_message(message_id)
    found = parts(raw, account, message_id)
    return {"account": account["emails"][0], "source": "local_thunderbird_mime_cache", "message_id": message_id,
            "attachments": [m for m, _ in found[offset:offset + limit]], "returned": len(found[offset:offset + limit]),
            "total_attachments": len(found), "has_more": len(found) > offset + limit,
            "next_offset": offset + limit if len(found) > offset + limit else None,
            "notice": "Local cached MIME only; missing/hashed folder layouts may be unsupported. No network download or document parsing."}


def source_attachment(message_id, attachment_id):
    if not re.fullmatch(r"a_[0-9a-f]{64}", attachment_id):
        raise BridgeError("Use an attachment ID from thunderbird_list_attachments.")
    raw, account = selected_message(message_id)
    for meta, part in parts(raw, account, message_id):
        if meta["id"] == attachment_id:
            if part.defects:
                raise BridgeError("Attachment MIME is malformed; original bytes cannot be verified.")
            payload = part.get_payload()
            if str(part.get("Content-Transfer-Encoding", "")).lower() != "base64" and isinstance(payload, str) and re.search(r"(?m)^>+From ", payload):
                raise BridgeError("Ambiguous mbox escaping in attachment; original bytes cannot be verified.")
            data = part.get_payload(decode=True)
            if not isinstance(data, bytes) or part.defects:
                raise BridgeError("Attachment MIME encoding is unavailable or malformed.")
            if len(data) > attachments.MAX_BYTES:
                raise BridgeError("Attachment exceeds the 10 MiB transfer limit.")
            current_profile, current_account = selection()
            if current_profile["id"] + current_account["fingerprint"] != account["cache_scope"]:
                raise BridgeError("Selected account changed during attachment access.")
            return data, {**meta, "account": account["emails"][0], "source": "local_thunderbird_mime_cache"}
    raise BridgeError("Attachment changed or is outside the selected message/account. List it again.")


def get_attachment(message_id, attachment_id, include_image=False):
    data, meta = source_attachment(message_id, attachment_id)
    return attachments.transfer(data, meta, lambda: source_attachment(message_id, attachment_id), include_image)
