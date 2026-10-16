"""Local publication checks; never contact a mail service or upload scan inputs."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import struct
import sys
import zlib

EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
USER_PATH = re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]+[^<%\s]|/(?:home|Users)/[^<%\s/]+)")
MAIL_SUFFIXES = {".eml", ".msg", ".pst", ".ost", ".sqlite", ".db", ".msf", ".mbox"}
PRIVATE_NAMES = {"prefs.js", "profiles.ini", "settings.json", "thunderbird.json", "outlook.json", ".env"}
PRIVATE_DIRS = {"private", "work", "outputs", "node_modules", "__pycache__", ".venv"}
MAX_BLOB = 2 * 1024 * 1024
# The existing icon's provenance certificate has a public CA contact. Exempt
# only that reviewed contact in this byte-identical asset, never private tokens.
PUBLIC_ASSET_EMAIL_HASHES = {
    "b00618f7292233a1643fada95523267c1e6635a8": {
        "864886422484e13ce2a6c684dec9701d102aab7afdb4a42668a3938165d89442",
    },
}


class GuardError(Exception):
    """A sanitized configuration or Git error; contains no inspected data."""


def git(root, *arguments):
    result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True)
    if result.returncode:
        raise GuardError("Git inspection failed; no upload was attempted.")
    return result.stdout


def load_denylist(root, supplied=None):
    configured = supplied or os.environ.get("MAIL_BRIDGE_PUBLICATION_DENY_FILE")
    if not configured:
        result = subprocess.run(["git", "-C", str(root), "config", "--local", "--get", "mailbridge.privateDenyFile"], capture_output=True)
        if result.returncode not in (0, 1):
            raise GuardError("Cannot inspect private publication configuration.")
        configured = result.stdout.decode("utf-8").strip() or None
    path = Path(configured) if configured else root / "private/publication-denylist.json"
    if not path.is_absolute():
        path = root / path
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if configured:
            raise GuardError("Configured private denylist is missing.") from None
        return []
    except (OSError, UnicodeError, ValueError):
        raise GuardError("Private denylist cannot be read.") from None
    if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
        raise GuardError("Private denylist must be an array of nonempty strings.")
    if configured and not values:
        raise GuardError("Configured private denylist is empty.")
    return values


def png_metadata(data):
    """Inspect metadata, not compressed pixels misdecoded as random text."""
    values = []
    offset = 8
    def inflate(value):
        decoder = zlib.decompressobj()
        result = decoder.decompress(value, MAX_BLOB + 1)
        if len(result) > MAX_BLOB or decoder.unconsumed_tail or not decoder.eof:
            raise GuardError("PNG metadata is invalid or exceeds the inspection limit.")
        return result
    while offset + 12 <= len(data):
        size = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            raise GuardError("Invalid PNG metadata structure.")
        value = data[offset + 8:offset + 8 + size]
        if kind == b"tEXt":
            values.append(value.replace(b"\0", b" "))
        elif kind == b"zTXt":
            name, separator, rest = value.partition(b"\0")
            if not separator or not rest or rest[0] != 0:
                raise GuardError("Invalid PNG metadata structure.")
            values.extend((name, inflate(rest[1:])))
        elif kind == b"iTXt":
            fields = value.split(b"\0", 5)
            if len(fields) != 6 or fields[1] not in (b"", b"\x01") or fields[2] != b"":
                raise GuardError("Invalid PNG metadata structure.")
            values.extend(fields[:1] + fields[3:5] + [inflate(fields[5]) if fields[1] else fields[5]])
        elif kind not in {b"IHDR", b"IDAT", b"IEND", b"PLTE"}:
            values.append(value)
        offset = end
        if kind == b"IEND":
            return b"\n".join(values)
    raise GuardError("Invalid PNG metadata structure.")


def text_views(data):
    # Catch ordinary text and common JSON/URL encodings without executing inputs.
    from urllib.parse import unquote
    is_png = data.startswith(b"\x89PNG\r\n\x1a\n")
    if is_png:
        data = png_metadata(data)
    views = [data.decode("utf-8", errors="replace")]
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        views.append(data.decode("utf-16", errors="replace"))
    elif not is_png and data[:1024].count(b"\x00") > len(data[:1024]) // 4:
        views.extend(data.decode(codec, errors="replace") for codec in ("utf-16-le", "utf-16-be"))
    for view in list(views):
        views.append(unquote(view))
        # Decode JSON Unicode escapes only; avoid interpreting arbitrary strings.
        views.append(re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), view))
    return views


def content_findings(data, denylist=(), *, commit=False):
    findings = set()
    if len(data) > MAX_BLOB:
        findings.add("oversized-object-needs-review")
    views = text_views(data)
    approved_emails = set()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        blob_id = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        approved_emails = PUBLIC_ASSET_EMAIL_HASHES.get(blob_id, set())
    for value in denylist:
        encoded = [value.encode(codec) for codec in ("utf-8", "utf-16-le", "utf-16-be")]
        encoded.append(base64.b64encode(value.encode("utf-8")))
        if any(value.casefold() in view.casefold() for view in views) or any(n.lower() in data.lower() for n in encoded):
            findings.add("private-denylist-match")
    for view in views:
        if USER_PATH.search(view):
            findings.add("personal-user-path")
        # Git identity headers can contain public author addresses. The private
        # denylist still checks the entire commit, including author/committer.
        message = view.partition("\n\n")[2] if commit else view
        if any(not match.casefold().endswith(".test")
               and hashlib.sha256(match.casefold().encode()).hexdigest() not in approved_emails
               for match in EMAIL.findall(message)):
            findings.add("non-test-email")
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{30,}|\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}", view):
            findings.add("credential-pattern")
    return sorted(findings)


def path_findings(name):
    path = PurePosixPath(name)
    parts = [p.casefold() for p in path.parts]
    findings = []
    if path.is_absolute() or ".." in parts:
        findings.append("unsafe-path")
    if (any(part in PRIVATE_DIRS or part.endswith(".sbd") for part in parts)
            or path.name.casefold() in PRIVATE_NAMES or path.name.casefold().startswith(".env.")
            or path.suffix.casefold() in MAIL_SUFFIXES or ".sqlite-" in path.name.casefold()):
        findings.append("private-or-mail-data-path")
    return findings


def tree_entries(root, tree):
    entries = []
    for item in git(root, "ls-tree", "-r", "-z", tree).split(b"\0"):
        if item:
            metadata, name = item.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split()
            entries.append((mode, kind, oid, name.decode("utf-8", errors="surrogateescape")))
    return entries


def inspect(root, *, staged=False, history=False, denylist=(), message_file=None):
    objects = {}
    commits = []
    findings = []
    trees = []
    if staged:
        trees.append(git(root, "write-tree").decode().strip())
    if history:
        commits = git(root, "rev-list", "--all").decode().splitlines()
        trees.extend(commits)
    for tree in trees:
        for mode, kind, oid, name in tree_entries(root, tree):
            # Report opaque IDs, never offending filenames or content.
            label = hashlib.sha256(name.encode("utf-8", errors="surrogateescape")).hexdigest()[:16]
            reasons = path_findings(name) + content_findings(name.encode("utf-8", errors="surrogateescape"), denylist)
            if mode not in {"100644", "100755"} or kind != "blob":
                reasons.append("symlink-or-submodule")
            findings.extend({"object": oid, "path_digest": label, "rule": reason} for reason in sorted(set(reasons)))
            if kind == "blob":
                objects[oid] = "blob"
    objects.update({oid: "commit" for oid in commits})
    for oid, kind in objects.items():
        size = int(git(root, "cat-file", "-s", oid).decode())
        if size > MAX_BLOB:
            findings.append({"object": oid, "rule": "oversized-object-needs-review"})
            continue
        data = git(root, "cat-file", kind, oid)
        findings.extend({"object": oid, "rule": reason}
                        for reason in content_findings(data, denylist, commit=kind == "commit"))
    if message_file is not None:
        try:
            data = Path(message_file).read_bytes()
        except OSError:
            raise GuardError("Commit message file cannot be read.") from None
        findings.extend({"object": "pending-commit-message", "rule": reason}
                        for reason in content_findings(data, denylist))
    unique = {json.dumps(f, sort_keys=True): f for f in findings}
    return {"ok": not unique, "commits_checked": len(commits), "objects_checked": len(objects),
            "private_denylist_loaded": bool(denylist), "findings": list(unique.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--staged", action="store_true", help="Check the complete staged tree")
    parser.add_argument("--all-history", action="store_true", help="Check every locally reachable commit and historical blob")
    parser.add_argument("--message-file", type=Path, help="Also check a pending commit message")
    parser.add_argument("--deny-file", type=Path, help="Local-only JSON array of protected strings; never commit it")
    args = parser.parse_args()
    try:
        root = args.repo.resolve()
        result = inspect(root, staged=args.staged, history=args.all_history or not args.staged,
                         denylist=load_denylist(root, args.deny_file), message_file=args.message_file)
    except (GuardError, OSError, ValueError):
        result = {"ok": False, "error": "Publication inspection failed. Check local Git and private denylist configuration."}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
