"""Thunderbird profile discovery and explicit per-user account selection."""
from __future__ import annotations

import configparser
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
from urllib.parse import unquote, urlsplit


class BridgeError(Exception):
    def __init__(self, message, *, code="mail_access_failed", retryable=False, next_action=None, details=None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.next_action = next_action
        self.details = details

    def as_dict(self):
        value = {"error": str(self), "code": self.code, "retryable": self.retryable}
        if self.next_action:
            value["next_action"] = self.next_action
        if self.details is not None:
            value["details"] = self.details
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


def profiles(*, diagnostic_state=None):
    found = {}
    state = diagnostic_state if diagnostic_state is not None else {}
    state.update(registries_unreadable=0, profiles_unavailable=0)
    for root in profile_roots():
        registry = root / "profiles.ini"
        try:
            if not registry.is_file():
                continue
        except OSError:
            state["registries_unreadable"] += 1
            continue
        parser = configparser.ConfigParser(interpolation=None)
        try:
            with registry.open(encoding="utf-8-sig") as source:
                parser.read_file(source)
            for section in parser.sections():
                if not section.startswith("Profile") or not parser.has_option(section, "Path"):
                    continue
                value = parser.get(section, "Path")
                path = Path(value).expanduser()
                if parser.get(section, "IsRelative", fallback="1") == "1":
                    path = root / path
                try:
                    path = path.resolve()
                    available = (path / "prefs.js").is_file()
                except OSError:
                    state["profiles_unavailable"] += 1
                    continue
                if not available:
                    state["profiles_unavailable"] += 1
                    continue
                token = "p_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
                found[token] = {"id": token, "name": parser.get(section, "Name", fallback=section), "path": path}
        except (OSError, UnicodeError, configparser.Error):
            state["registries_unreadable"] += 1
            continue
    return list(found.values())


def _installation_candidates():
    """Read executable registrations only; never execute a mail client."""
    candidates = []
    for name in ("thunderbird", "thunderbird.exe"):
        located = shutil.which(name)
        if located:
            candidates.append(Path(located))
    if sys.platform == "win32":
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                try:
                    with winreg.OpenKey(hive, r"Software\Microsoft\Windows\CurrentVersion\App Paths\thunderbird.exe",
                                        0, winreg.KEY_READ | view) as key:
                        value, _ = winreg.QueryValueEx(key, "")
                    if isinstance(value, str) and value.strip():
                        candidates.append(Path(os.path.expandvars(value.strip().strip('"'))))
                except OSError:
                    continue
        for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(variable)
            if base:
                candidates.append(Path(base) / "Mozilla Thunderbird/thunderbird.exe")
    elif sys.platform == "darwin":
        candidates.extend([Path("/Applications/Thunderbird.app/Contents/MacOS/thunderbird"),
                           Path.home() / "Applications/Thunderbird.app/Contents/MacOS/thunderbird"])
    else:
        candidates.extend([Path("/snap/bin/thunderbird"), Path("/var/lib/snapd/snap/bin/thunderbird"),
                           Path("/var/lib/flatpak/app/org.mozilla.Thunderbird/current/active/files/bin/thunderbird"),
                           Path.home() / ".local/share/flatpak/app/org.mozilla.Thunderbird/current/active/files/bin/thunderbird"])
    return candidates


def installation_status():
    """Return evidence, not paths or a claim that portable installs cannot exist."""
    uncertain = False
    try:
        candidates = _installation_candidates()
    except (OSError, ValueError):
        candidates, uncertain = [], True
    for path in candidates:
        try:
            if path.is_file():
                return {"state": "detected", "note": "A registered or discoverable Thunderbird executable exists; it was not started."}
        except OSError:
            uncertain = True
    return {"state": "unconfirmed" if uncertain else "not_detected",
            "note": "Thunderbird installation could not be confirmed. Portable or custom installations may not be detected; existing local profiles can still be used."}


def diagnostics():
    """Inspect local setup metadata without reading mail, identities or paths into output."""
    installation = installation_status()
    discovery = {}
    discovered = profiles(diagnostic_state=discovery)
    account_count = index_count = unreadable = 0
    for profile in discovered:
        try:
            configured = read_accounts(profile)
            account_count += len(configured)
            if configured and (profile["path"] / "global-messages-db.sqlite").is_file():
                index_count += 1
        except (OSError, ValueError, TypeError):
            unreadable += 1
    saved = selection_path().is_file()
    if not discovered:
        if discovery.get("registries_unreadable", 0) or discovery.get("profiles_unavailable", 0):
            code, action = "thunderbird_profile_unconfirmed", "check_thunderbird_profile_access"
            guidance = "Thunderbird profile registration exists but could not be read or resolved. Check the profile registry, configuration and permissions, then run diagnostics again; reinstalling is not established as necessary."
        elif installation["state"] == "not_detected":
            code, action = "thunderbird_not_detected", "install_thunderbird"
            guidance = "Thunderbird installation and a usable registered profile were not detected. Install Thunderbird from https://www.thunderbird.net/, open it and register an IMAP/POP3 account. For an existing portable/custom profile, set THUNDERBIRD_HOME to its registry location."
        else:
            code, action = "thunderbird_profile_unconfirmed", "open_thunderbird_and_register_account"
            guidance = "A usable registered Thunderbird profile could not be confirmed. Open Thunderbird and complete profile/account setup, or check the existing profile registry location and permissions."
    elif account_count == 0:
        code = "account_registration_unconfirmed"
        if unreadable:
            action = "check_thunderbird_profile_access"
            guidance = "Thunderbird account registration could not be confirmed because profile configuration could not be read. Check profile permissions and configuration, then run diagnostics again."
        else:
            action = "register_thunderbird_account"
            guidance = "No supported IMAP/POP3 account registration could be confirmed. Open Thunderbird, add or complete the intended mail account and sign in, then run diagnostics again. Unsupported account types may also cause this result."
    elif not index_count:
        code, action = "thunderbird_index_missing", "enable_indexing_and_sync"
        guidance = "Registered Thunderbird accounts were found, but no local global search index was detected for them. Enable Global Search and Indexer in Thunderbird, sync needed mail and allow indexing to finish."
    elif not saved:
        code, action = "selection_required", "discover_and_select_account"
        guidance = "Local account configuration and an index exist. Use thunderbird_profiles and thunderbird_accounts, then ask for an explicit profile/account choice before selecting it."
    else:
        code, action = "selection_saved", "check_thunderbird_status"
        guidance = "Local account configuration, an index and a saved bridge selection exist. Run thunderbird_status to validate that selected account; saved settings do not prove current account availability or authentication."
    return {"installation": installation, "profile_count": len(discovered),
            "account_count": account_count, "profiles_with_index": index_count,
            "profiles_unreadable": unreadable + discovery.get("registries_unreadable", 0) + discovery.get("profiles_unavailable", 0),
            "selection_saved": saved,
            "code": code, "next_action": action, "guidance": guidance,
            "authentication_verified": False, "mail_read": False, "client_started": False,
            "note": "Counts describe local IMAP/POP3 configuration only. No passwords, account identities, profile paths, mail or server login checks are returned. Existing cached data does not require a detected executable."}


def profile_by_id(profile_id):
    for profile in profiles():
        if profile["id"] == profile_id:
            return profile
    raise BridgeError("The selected Thunderbird profile could not be confirmed. Run thunderbird_diagnostics, then discover profiles again.",
                      code="thunderbird_profile_unconfirmed", next_action="run_thunderbird_diagnostics")


def read_accounts(profile):
    prefs = {}
    pattern = re.compile(r'^user_pref\("(mail\.(?:identity\.[^.]+\.(?:useremail|fcc_folder|draft_folder|archive_folder|stationery_folder)|account\.[^.]+\.(?:server|identities)|server\.[^.]+\.(?:hostname|userName|type|port)))", (.+)\);$')
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
        identity_ids = [value.strip() for value in str(prefs.get("mail.account." + account_id + ".identities", "")).split(",")]
        emails = [prefs["mail.identity." + identity + ".useremail"] for identity in identity_ids
                  if isinstance(prefs.get("mail.identity." + identity + ".useremail"), str)]
        if not emails:
            continue
        account = {"id": account_id, "emails": emails, "host": host.casefold(),
                   "username": user, "type": kind, "port": prefs.get(base + "port")}
        canonical = json.dumps(account, sort_keys=True, ensure_ascii=False)
        account["fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
        # Folder preferences may change without changing the selected identity.
        # Never infer roles from localized names or extend account scope.
        roles = {}
        for identity in identity_ids:
            for pref, role in (("fcc_folder", "sent"), ("draft_folder", "drafts"),
                               ("archive_folder", "archive"), ("stationery_folder", "templates")):
                uri = prefs.get("mail.identity." + identity + "." + pref)
                if isinstance(uri, str) and allowed_uri(uri, account):
                    key = folder_key(uri, account)
                    roles[key] = role if key not in roles or roles[key] == role else "other"
        account["folder_roles"] = roles
        accounts.append(account)
    return accounts


def account_by_id(profile, account_id):
    for account in read_accounts(profile):
        if account["id"] == account_id:
            return account
    raise BridgeError("The selected Thunderbird account registration could not be confirmed. Check that its IMAP/POP3 account is configured, then explicitly select it again.",
                      code="account_registration_unconfirmed", next_action="run_thunderbird_diagnostics")


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


def folder_key(uri, account):
    parts = urlsplit(uri)
    return (parts.scheme, (parts.hostname or "").casefold(), unquote(parts.username or ""),
            parts.port or account.get("port"), unquote(parts.path))


def folder_role(uri, account):
    key = folder_key(uri, account)
    configured = account.get("folder_roles", {}).get(key)
    if configured:
        # A user can store sent/archive copies in the inbox. It then has mixed
        # roles; callers must not exclude all received mail as sent copies.
        return "other" if key[-1].casefold() == "/inbox" else configured
    return "inbox" if key[-1].casefold() == "/inbox" else "other"


@contextmanager
def database():
    profile, account = selection()
    path = profile["path"] / "global-messages-db.sqlite"
    if not path.is_file():
        raise BridgeError("Thunderbird's local index is missing. Enable Global Search and Indexer, sync needed mail and wait for indexing.",
                          code="thunderbird_index_missing", next_action="enable_indexing_and_sync")
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
        for folder in folders:
            folder["role"] = folder_role(folder["folderURI"], account)
        if not folders:
            raise BridgeError("The selected account has no indexed folders. Enable indexing and sync Thunderbird.")
        yield db, folders, profile, account
    finally:
        db.close()
