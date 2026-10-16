"""Classic Outlook through Windows PowerShell and the documented COM API."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from accounts import BridgeError

NOTICE = ("Classic Outlook desktop store only; Microsoft 365 subscription is not required. "
          "Searches are bounded and report scan_incomplete when partial. Outlook may fetch data "
          "through its configured provider; offline operation or complete sync is not guaranteed. "
          "No send, delete, move, mark-read, draft-save, or attachment-content operations.")


def settings_path():
    override = os.environ.get("MAIL_BRIDGE_OUTLOOK_SETTINGS")
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    return Path(override).expanduser() if override else root / "CypSoft/MailBridge/outlook.json"


def backend(operation, **arguments):
    if sys.platform != "win32":
        raise BridgeError("Outlook requires Windows and a running classic Outlook desktop profile.")
    system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
    executable = system_root / "System32/WindowsPowerShell/v1.0/powershell.exe"
    script = Path(__file__).with_suffix(".ps1")
    try:
        result = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-STA", "-File", str(script)],
            input=json.dumps({"operation": operation, **arguments}, ensure_ascii=False),
            capture_output=True, text=True, encoding="utf-8", timeout=45,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), shell=False)
        data = json.loads(result.stdout.lstrip("\ufeff"))
    except subprocess.TimeoutExpired:
        raise BridgeError("Outlook did not respond. Check its security/access prompt or profile, then retry. Security settings are never changed.") from None
    except (OSError, UnicodeError, ValueError):
        raise BridgeError("Could not read Outlook. Open classic Outlook and check Windows PowerShell/script policy. No security policy is bypassed.") from None
    if result.returncode or not isinstance(data, dict) or not data.get("ok"):
        code = data.get("error") if isinstance(data, dict) else None
        explanations = {
            "shared_delivery_store": "Multiple Outlook accounts share a delivery store; this layout cannot safely isolate one account.",
            "selection_changed": "Outlook account/profile identity changed. Discover and explicitly select the account again.",
            "message_outside_scope": "Message is outside the selected Outlook account or in an excluded folder.",
            "folder_outside_scope": "Folder is outside the selected Outlook account scope.",
            "invalid_message_id": "Use a message ID returned by Outlook search.",
        }
        raise BridgeError(explanations.get(code, "Outlook access failed. Check the running classic profile and security prompt. Nothing was sent or changed."))
    return data["result"]


def accounts():
    result = backend("accounts")
    return {"accounts": [{k: v for k, v in row.items() if k != "fingerprint"} for row in result["accounts"]],
            "outlook_version": result["outlook_version"],
            "note": "Account names/addresses are shared with the AI host. Select ONE supported account explicitly."}


def selection():
    try:
        saved = json.loads(settings_path().read_text(encoding="utf-8"))
        if (not isinstance(saved, dict) or saved.get("version") != 1 or
            not re.fullmatch(r"o_[0-9a-f]{24}", saved.get("account_id", "")) or
            not re.fullmatch(r"[0-9a-f]{64}", saved.get("fingerprint", ""))):
            raise ValueError()
        return {k: saved[k] for k in ("account_id", "fingerprint")}
    except FileNotFoundError:
        raise BridgeError("No Outlook account selected. Discover accounts and explicitly select one first.") from None
    except (KeyError, TypeError, ValueError):
        raise BridgeError("Invalid local Outlook selection. Select an account again.") from None


def select_account(account_id, confirm=False):
    if confirm is not True:
        raise BridgeError("An explicit Outlook account choice is required; confirm must be true.")
    rows = backend("accounts")["accounts"]
    choices = [row for row in rows if row["id"] == account_id and row["supported"]]
    if len(choices) != 1:
        raise BridgeError("Choose a supported Outlook account from outlook_accounts. Shared delivery stores are unsupported.")
    row = choices[0]
    backend("validate", account_id=row["id"], fingerprint=row["fingerprint"])
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + os.urandom(8).hex() + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as target:
            if os.name != "nt":
                os.chmod(temporary, 0o600)
            json.dump({"version": 1, "account_id": row["id"], "fingerprint": row["fingerprint"]}, target, indent=2)
            target.write("\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return {"configured": True, "account": row["address"], "scope": "Only this account's unique delivery store. No Outlook data changed."}


def response(value):
    return {"source": "classic_outlook_object_model", "notice": NOTICE, **value}


def status():
    if not settings_path().is_file():
        return response({"configured": False, "next_step": "Discover Outlook accounts and explicitly select one."})
    return response(backend("status", **selection()))


def boundary(value):
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if parsed.strftime("%Y-%m-%d") != value:
            raise ValueError()
        return parsed.isoformat()
    except ValueError:
        raise BridgeError("Dates must be valid YYYY-MM-DD dates in UTC.") from None


def scan(*, query="", sender="", recipient="", folder_id="", after="", before="", field="any",
         limit=10, offset=0, scan_limit=1000, conversation_id="", body_limit=6000):
    start, end = boundary(after), boundary(before)
    if start and end and end <= start:
        raise BridgeError("before must be later than after.")
    include_body = bool(conversation_id or query and field != "subject")
    value = backend("scan", **selection(), folder_id=folder_id, after=start, before=end,
                    include_body=include_body, max_characters=body_limit, scan_limit=scan_limit,
                    conversation_id=conversation_id)
    matches = []
    words = query.casefold().split()
    for message in value["messages"]:
        if sender.casefold() not in message["sender"].casefold() or recipient.casefold() not in message["recipients"].casefold():
            continue
        fields = {"subject": message["subject"], "body": message.get("body", "")}
        text = fields.get(field, " ".join([message["subject"], message.get("body", ""), message["sender"], message["recipients"], *message["attachment_names"]])).casefold()
        if not all(word in text for word in words):
            continue
        if conversation_id and message["conversation_id"] != conversation_id:
            continue
        matches.append(message)
    matches.sort(key=lambda m: (m["date"], m["id"]), reverse=not bool(conversation_id))
    shown = matches[offset:offset + limit]
    for message in shown:
        if not conversation_id:
            body = message.pop("body", "")
            message["snippet"] = " ".join(body.split())[:280]
    more = len(matches) > offset + limit
    return response({"account": value["account"], "messages": shown, "returned": len(shown),
                     "has_more": more, "next_offset": offset + limit if more else None,
                     "scan_incomplete": value["scan_incomplete"], "scanned_messages": value["scanned_messages"],
                     "search_body_character_limit": body_limit if include_body else 0})


def search(query="", sender="", recipient="", folder_id="", after="", before="", field="any", limit=10, offset=0, scan_limit=1000):
    return scan(query=query, sender=sender, recipient=recipient, folder_id=folder_id, after=after,
                before=before, field=field, limit=limit, offset=offset, scan_limit=scan_limit)


def read(message_id, max_characters=16000):
    if not re.fullmatch(r"[0-9A-Fa-f]{16,4096}", message_id):
        raise BridgeError("Use an Outlook message ID from search.")
    return response(backend("read", **selection(), message_id=message_id, max_characters=max_characters))


def thread(thread_id, limit=20, offset=0, max_characters_per_message=6000, scan_limit=1000):
    return scan(conversation_id=thread_id, limit=limit, offset=offset,
                body_limit=max_characters_per_message, scan_limit=scan_limit)
