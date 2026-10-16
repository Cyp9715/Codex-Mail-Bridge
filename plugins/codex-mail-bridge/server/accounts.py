"""Thunderbird profile discovery and explicit per-user account selection."""
from __future__ import annotations

import configparser
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from urllib.parse import unquote, urlsplit


class BridgeError(Exception):
    def __init__(self, message, *, code="mail_access_failed", retryable=False, next_action=None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.next_action = next_action

    def as_dict(self):
        value = {"error": str(self), "code": self.code, "retryable": self.retryable}
        if self.next_action:
            value["next_action"] = self.next_action
        return value


def settings_path():
    override = os.environ.get("MAIL_BRIDGE_THUNDERBIRD_SETTINGS") or os.environ.get("THUNDERBIRD_BRIDGE_SETTINGS")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "CypSoft/MailBridge/thunderbird.json"


def selection_path():
    """Read a prior selection without changing files during a read-only tool call."""
    path = settings_path()
    if os.environ.get("MAIL_BRIDGE_THUNDERBIRD_SETTINGS") or os.environ.get("THUNDERBIRD_BRIDGE_SETTINGS") or path.exists():
        return path
    # Previous releases stored the same opaque selection outside the package.
    for name in ("ThunderbirdBridge", "ThunderbirdMailBridge"):
        previous = path.parent.parent / name / "settings.json"
        if previous.is_file():
            return previous
    return path


def profile_roots():
    if os.environ.get("THUNDERBIRD_HOME"):
        return [Path(os.environ["THUNDERBIRD_HOME"]).expanduser()]
    if sys.platform == "win32":
        return [Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "Thunderbird"]
    if sys.platform == "darwin":
        return [Path.home() / "Library/Thunderbird"]
    return [Path.home() / ".thunderbird",
            Path.home() / "snap/thunderbird/common/.thunderbird",
            Path.home() / ".var/app/org.mozilla.Thunderbird/.thunderbird"]


def profiles():
    found = {}
    for root in profile_roots():
        registry = root / "profiles.ini"
        if not registry.is_file():
            continue
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read(registry, encoding="utf-8-sig")
            for section in parser.sections():
                if not section.startswith("Profile") or not parser.has_option(section, "Path"):
                    continue
                value = parser.get(section, "Path")
                path = Path(value).expanduser()
                if parser.get(section, "IsRelative", fallback="1") == "1":
                    path = root / path
                path = path.resolve()
                if not (path / "prefs.js").is_file():
                    continue
                token = "p_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
                found[token] = {"id": token, "name": parser.get(section, "Name", fallback=section), "path": path}
        except (OSError, UnicodeError, configparser.Error):
            continue
    return list(found.values())


def profile_by_id(profile_id):
    for profile in profiles():
        if profile["id"] == profile_id:
            return profile
    raise BridgeError("Thunderbird profile was not found. Run thunderbird_profiles again.")


def read_accounts(profile):
    prefs = {}
    pattern = re.compile(r'^user_pref\("(mail\.(?:identity\.[^.]+\.useremail|account\.[^.]+\.(?:server|identities)|server\.[^.]+\.(?:hostname|userName|type|port)))", (.+)\);$')
    with (profile["path"] / "prefs.js").open(encoding="utf-8") as source:
        for line in source:
            match = pattern.match(line.strip())
            if match:
                value = json.loads(match[2])
                if isinstance(value, (str, int)):
                    prefs[match[1]] = value
    accounts = []
    for key, server_id in prefs.items():
        if not key.startswith("mail.account.") or not key.endswith(".server"):
            continue
        account_id = key.split(".")[2]
        base = "mail.server." + str(server_id) + "."
        kind = prefs.get(base + "type")
        if kind not in ("imap", "pop3"):
            continue
        host, user = prefs.get(base + "hostname"), prefs.get(base + "userName")
        if not isinstance(host, str) or not isinstance(user, str) or not host or not user:
            continue
        identity_ids = str(prefs.get("mail.account." + account_id + ".identities", "")).split(",")
        emails = [prefs["mail.identity." + identity + ".useremail"] for identity in identity_ids
                  if isinstance(prefs.get("mail.identity." + identity + ".useremail"), str)]
        if not emails:
            continue
        account = {"id": account_id, "emails": emails, "host": host.casefold(),
                   "username": user, "type": kind, "port": prefs.get(base + "port")}
        canonical = json.dumps(account, sort_keys=True, ensure_ascii=False)
        account["fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
        accounts.append(account)
    return accounts


def account_by_id(profile, account_id):
    for account in read_accounts(profile):
        if account["id"] == account_id:
            return account
    raise BridgeError("Selected account is unavailable or unsupported. IMAP and POP3 identities are supported.")


def selection():
    try:
        saved = json.loads(selection_path().read_text(encoding="utf-8"))
        if not isinstance(saved, dict) or saved.get("version") != 1:
            raise BridgeError("Unsupported local selection file. Select an account again.")
        profile = profile_by_id(saved["profile_id"])
        account = account_by_id(profile, saved["account_id"])
        if saved["fingerprint"] != account["fingerprint"]:
            raise BridgeError("Account identity changed. Select it again before accessing mail.")
        return profile, account
    except FileNotFoundError:
        raise BridgeError("No account selected. Discover profiles/accounts and explicitly select one first.",
                          code="selection_required", next_action="discover_and_select_account") from None
    except (KeyError, TypeError, json.JSONDecodeError):
        raise BridgeError("Local selection file is invalid. Select an account again.") from None


def select_account(profile_id, account_id, confirm=False):
    if confirm is not True:
        raise BridgeError("An explicit account choice is required; confirm must be true.")
    profile = profile_by_id(profile_id)
    account = account_by_id(profile, account_id)
    saved = {"version": 1, "profile_id": profile["id"], "account_id": account["id"],
             "fingerprint": account["fingerprint"]}
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation and atomic replacement; no mailbox changes.
    temp = path.with_name(path.name + "." + os.urandom(8).hex() + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as target:
            if os.name != "nt":
                os.chmod(temp, 0o600)
            json.dump(saved, target, indent=2)
            target.write("\n")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return {"configured": True, "account": account["emails"][0], "account_id": account["id"],
            "scope": "Only this account's indexed folders are accessible.",
            "settings": "Saved outside the plugin package in the current user's application settings."}


def allowed_uri(uri, account):
    try:
        parts = urlsplit(uri)
        expected_scheme = "imap" if account["type"] == "imap" else "mailbox"
        return (parts.scheme == expected_scheme and (parts.hostname or "").casefold() == account["host"]
                and unquote(parts.username or "") == account["username"]
                and parts.password is None and parts.port in (None, account["port"]))
    except (TypeError, ValueError):
        return False


@contextmanager
def database():
    profile, account = selection()
    path = profile["path"] / "global-messages-db.sqlite"
    if not path.is_file():
        raise BridgeError("Thunderbird's local index is missing. Enable Global Search and Indexer, then wait for indexing.")
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=3)
    try:
        db.row_factory = sqlite3.Row
        db.create_function("casefold", 1, lambda value: str(value or "").casefold(), deterministic=True)
        db.execute("PRAGMA query_only = ON")
        deadline = time.monotonic() + 8
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        db.execute("BEGIN")
        folders = [dict(row) for row in db.execute("SELECT id, folderURI, name FROM folderLocations")
                   if allowed_uri(row["folderURI"], account)]
        if not folders:
            raise BridgeError("The selected account has no indexed folders. Enable indexing and sync Thunderbird.")
        yield db, folders, profile, account
    finally:
        db.close()
