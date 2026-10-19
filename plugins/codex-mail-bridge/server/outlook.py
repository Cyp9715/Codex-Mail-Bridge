"""Classic Outlook through Windows PowerShell and the documented COM API."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from accounts import BridgeError
import attachments
from mail_dates import resolve_range
from mail_output import bounded_metadata, budget_bodies, folder_page, message_identity

NOTICE = ("Access uses local Windows PowerShell/COM; Computer Use is not required. "
          "Sign in and sync in classic Outlook first, then keep it running. "
          "Searches are bounded and report scan_incomplete when partial. Outlook may fetch data "
          "through its configured provider; offline operation or complete sync is not guaranteed. "
          "No send, delete, move, mark-read, or draft-save operations. Attachments are transferred as original files, never parsed or executed.")


def settings_path():
    override = os.environ.get("MAIL_BRIDGE_OUTLOOK_SETTINGS")
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    return Path(override).expanduser() if override else root / "CypSoft/MailBridge/outlook.json"


def powershell_environment():
    # A Python child of PowerShell 7 can inherit incompatible module paths.
    # Let Windows PowerShell discover its own defaults; preserve policy variables.
    return {key: value for key, value in os.environ.items() if key.upper() != "PSMODULEPATH"}


def backend(operation, **arguments):
    if sys.platform != "win32":
        raise BridgeError("Outlook requires Windows and a running classic Outlook desktop profile.",
                          code="unsupported_platform", next_action="use_windows_classic_outlook")
    system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
    executable = system_root / "System32/WindowsPowerShell/v1.0/powershell.exe"
    script = Path(__file__).with_suffix(".ps1")
    try:
        result = subprocess.run([str(executable), "-NoProfile", "-NonInteractive", "-STA", "-File", str(script)],
            input=json.dumps({"operation": operation, **arguments}, ensure_ascii=False),
            capture_output=True, text=True, encoding="utf-8", timeout=45,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), shell=False,
            env=powershell_environment())
        data = json.loads(result.stdout.lstrip("\ufeff"))
    except subprocess.TimeoutExpired:
        raise BridgeError("Outlook did not respond. Run outlook_diagnostics once. If a login, profile or security/access prompt is present, the user must handle it in Outlook before retrying. Do not use Computer Use or change security settings.",
                          code="provider_timeout", next_action="user_check_outlook_then_retry",
                          details={"recovery_operation": "outlook_diagnostics", "computer_use_required": False}) from None
    except (OSError, UnicodeError, ValueError):
        raise BridgeError("Could not run the Outlook CLI adapter. Check Windows PowerShell 5.1 and its existing script policy. Report the blocker without Computer Use or a policy bypass.",
                          code="runtime_unavailable", next_action="check_runtime_compatibility") from None
    if result.returncode or not isinstance(data, dict) or not data.get("ok"):
        code = data.get("error") if isinstance(data, dict) else None
        explanations = {
            "outlook_not_running": "Classic Outlook is not running in this Windows session. Run outlook_diagnostics, then outlook_start for an existing configured profile, and retry the operation.",
            "classic_outlook_not_installed": "Classic Outlook was not found in Windows App Paths. New/web Outlook cannot provide this COM adapter.",
            "outlook_profile_required": "Configure and sign in to a classic Outlook profile yourself, then retry. The bridge does not create profiles or automate login.",
            "outlook_start_timeout": "Classic Outlook has not started yet. Run outlook_diagnostics before retrying; the user must handle any profile/login prompt.",
            "outlook_instance_ambiguous": "Multiple classic Outlook processes are running in this Windows session. Resolve the intended instance before retrying.",
            "outlook_access_denied": "Outlook denied COM access. The user must resolve any security/access prompt or organization policy. Do not use Computer Use or weaken security settings.",
            "outlook_busy": "Classic Outlook is busy or rejected the COM call. Retry once after it becomes ready; do not switch to Computer Use.",
            "shared_delivery_store": "Multiple Outlook accounts share a delivery store; this layout cannot safely isolate one account.",
            "selection_changed": "Outlook account/profile identity changed. Discover and explicitly select the account again.",
            "message_outside_scope": "Message is outside the selected Outlook account or in an excluded folder.",
            "folder_outside_scope": "Folder is outside the selected Outlook account scope.",
            "invalid_message_id": "Use a message ID returned by Outlook search.",
            "candidate_scan_timeout": "Outlook metadata scan timed out. Narrow the date range or selected folder and retry.",
            "protected_message": "Encrypted/protected Outlook attachments are not transferred.",
            "invalid_attachment_id": "Use an attachment ID returned by the selected message's attachment list.",
            "unsupported_attachment": "Only by-value attachments within max_bytes can be transferred (default 10 MiB, maximum 100 MiB); linked, OLE and embedded-message attachments are unsupported.",
            "attachment_changed": "Attachment changed or is outside this message/account. List it again.",
            "attachment_data_unavailable": "The Outlook provider did not expose the original attachment bytes within the size limit.",
            "body_changed": "Message body changed between reads. Restart reading this message.",
        }
        action = {
            "outlook_not_running": "start_outlook", "classic_outlook_not_installed": "install_classic_outlook",
            "outlook_profile_required": "user_setup_outlook_profile", "outlook_start_timeout": "run_outlook_diagnostics",
            "outlook_instance_ambiguous": "resolve_outlook_instances", "outlook_access_denied": "user_resolve_outlook_access",
            "outlook_busy": "retry_operation_once", "candidate_scan_timeout": "narrow_filters_or_retry",
            "attachment_changed": "list_attachments_again", "body_changed": "restart_message_read",
        }.get(code, "run_outlook_diagnostics")
        raise BridgeError(explanations.get(code, "Outlook COM access failed. Run outlook_diagnostics once; the user must resolve any login, profile or security prompt. Do not fall back to Computer Use."),
                          code=code if code in explanations else "provider_unavailable",
                          retryable=code in {"candidate_scan_timeout", "outlook_busy", "outlook_start_timeout"}, next_action=action,
                          details={"recovery_operation": "outlook_diagnostics", "computer_use_required": False})
    if not isinstance(data.get("result"), dict):
        raise BridgeError("Outlook CLI returned an invalid response.", code="invalid_provider_response",
                          next_action="run_outlook_diagnostics")
    return data["result"]


def diagnostics():
    """Inspect installation/process state without COM activation or mailbox access."""
    return backend("diagnostics")


def start():
    """Explicit, idempotent launch of an already configured desktop client."""
    return backend("start")


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
        raise BridgeError("No Outlook account selected. Discover accounts and explicitly select one first.",
                          code="selection_required", next_action="discover_and_select_account") from None
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


def status(folder_limit=50, folder_offset=0):
    if not settings_path().is_file():
        return response({"configured": False, "next_step": "Discover Outlook accounts and explicitly select one."})
    value = backend("status", **selection())
    value.update(folder_page(value.pop("folders", []), folder_limit, folder_offset))
    return response(value)


def scan(*, query="", sender="", recipient="", folder_id="", after="", before="", field="any",
         limit=10, offset=0, scan_limit=1000, conversation_id="", body_limit=6000, attachment_query=None,
         include_snippet=False, scan_offset=0, max_total_characters=24000):
    dates = resolve_range(after, before)
    include_body = bool(conversation_id or include_snippet or query and field in {"any", "body"})
    value = backend("scan", **selection(), folder_id=folder_id, after=dates["after"] or "", before=dates["before"] or "",
                    include_body=include_body, max_characters=body_limit, scan_limit=scan_limit,
                    conversation_id=conversation_id, scan_offset=scan_offset,
                    include_recipient_details=bool(recipient or query and field in {"any", "metadata"} or conversation_id),
                    include_attachment_names=bool(attachment_query is not None or query and field in {"any", "metadata"} or conversation_id),
                    attachments_only=attachment_query is not None)
    matches = []
    body_matching = bool(query and field in {"any", "body"})
    recipient_matching = bool(recipient or query and field in {"any", "metadata"})
    attachment_matching = attachment_query is not None or bool(query and field in {"any", "metadata"})
    body_incomplete = sum(bool(m.get("body_truncated")) for m in value["messages"]) if body_matching else 0
    metadata_incomplete = sum(bool(recipient_matching and m.get("recipients_truncated") or
                                   attachment_matching and m.get("attachments_truncated")) for m in value["messages"])
    words = query.casefold().split()
    for message in value["messages"]:
        if sender.casefold() not in message["sender"].casefold() or recipient.casefold() not in message["recipients"].casefold():
            continue
        fields = {"subject": message["subject"], "body": message.get("body", ""),
                  "metadata": " ".join([message["subject"], message["sender"], message["recipients"], *message["attachment_names"]])}
        text = fields.get(field, " ".join([message["subject"], message.get("body", ""), message["sender"], message["recipients"], *message["attachment_names"]])).casefold()
        if not all(word in text for word in words):
            continue
        if attachment_query is not None:
            names = message["attachment_names"]
            if not names or not all(word in " ".join(names).casefold() for word in attachment_query.casefold().split()):
                continue
        if conversation_id and message["conversation_id"] != conversation_id:
            continue
        matches.append(message)
    matches.sort(key=lambda m: (m["date"], m["id"]), reverse=not bool(conversation_id))
    shown = matches[offset:offset + limit]
    for message in shown:
        if not conversation_id:
            body = message.pop("body", "")
            if include_snippet and attachment_query is None:
                message["snippet"] = " ".join(body.split())[:280]
            for key in ("body_characters", "body_offset", "body_offset_unit", "body_sha256", "has_more_body", "next_body_offset"):
                message.pop(key, None)
        bounded_metadata(message_identity(message, "outlook", value["account"]))
    more = len(matches) > offset + limit
    budget = budget_bodies(shown, max_total_characters) if conversation_id else {}
    return response({"account": value["account"], "messages": shown, "returned": len(shown),
                     "has_more": more, "next_offset": offset + limit if more else None,
                     "scan_incomplete": value["scan_incomplete"], "scanned_messages": value["scanned_messages"],
                     "match_evaluation_incomplete": bool(body_incomplete or metadata_incomplete),
                     "search_incomplete": bool(value["scan_incomplete"] or body_incomplete or metadata_incomplete),
                     "body_matching_truncated_messages": body_incomplete,
                     "metadata_matching_truncated_messages": metadata_incomplete,
                     "coverage_scope": "selected_local_store",
                     "scan_offset": scan_offset, "next_scan_offset": value.get("next_scan_offset"),
                     "scan_continuation_note": "Paginate matching results in this window first; then use next_scan_offset with offset 0 and identical filters. Mail changes can shift windows. Narrow dates/folders if time or offset limits are reached.",
                     "date_range": dates, **budget,
                     "search_body_character_limit": body_limit if include_body else 0})


def search(query="", sender="", recipient="", folder_id="", after="", before="", field="any", limit=10, offset=0, scan_limit=1000,
           include_snippet=False, scan_offset=0, body_search_limit=6000):
    return scan(query=query, sender=sender, recipient=recipient, folder_id=folder_id, after=after,
                before=before, field=field, limit=limit, offset=offset, scan_limit=scan_limit,
                include_snippet=include_snippet, scan_offset=scan_offset, body_limit=body_search_limit)


def search_attachments(query="", filename="", sender="", recipient="", folder_id="", after="", before="", limit=10, offset=0, scan_limit=1000,
                       scan_offset=0):
    value = scan(query=query, sender=sender, recipient=recipient, folder_id=folder_id, after=after,
                 before=before, field="subject", limit=limit, offset=offset, scan_limit=scan_limit,
                 attachment_query=filename, scan_offset=scan_offset)
    value["search_mode"] = "subject_and_attachment_metadata_only"
    value["attachment_search_note"] = "Bounded metadata scan only; refine subject/date/sender/filename filters. No body or file contents are read by this search."
    return value


def read(message_id, max_characters=16000, body_offset=0, expected_body_sha256=None):
    if not re.fullmatch(r"[0-9A-Fa-f]{16,4096}", message_id):
        raise BridgeError("Use an Outlook message ID from search.")
    value = backend("read", **selection(), message_id=message_id, max_characters=max_characters, body_offset=body_offset,
                    expected_body_sha256=expected_body_sha256 or "")
    bounded_metadata(message_identity(value["message"], "outlook", value["account"]))
    return response(value)


def thread(thread_id, limit=20, offset=0, max_characters_per_message=6000, scan_limit=1000,
           max_total_characters=24000, scan_offset=0):
    return scan(conversation_id=thread_id, limit=limit, offset=offset,
                body_limit=max_characters_per_message, scan_limit=scan_limit,
                max_total_characters=max_total_characters, scan_offset=scan_offset)


def attachment_request(operation, message_id, **arguments):
    if not re.fullmatch(r"[0-9A-Fa-f]{16,4096}", message_id):
        raise BridgeError("Use an Outlook message ID from search.")
    chosen = selection()
    value = backend(operation, **chosen, message_id=message_id, **arguments)
    if selection() != chosen:
        raise BridgeError("Selected Outlook account changed during attachment access.")
    return value


def list_attachments(message_id, limit=20, offset=0):
    value = attachment_request("attachments", message_id)
    entries = value["attachments"]
    for item in entries:
        if item.get("content_type") == "application/ms-tnef" or item["name"].casefold() == "winmail.dat":
            item.update(attachments.handoff_hints(item["name"], item.get("content_type", "")))
    value.update(attachments=entries[offset:offset + limit], returned=len(entries[offset:offset + limit]),
                 listed_attachment_count=len(entries), has_more=len(entries) > offset + limit,
                 next_offset=offset + limit if len(entries) > offset + limit else None)
    return response(value)


def get_attachment(message_id, attachment_id, max_bytes=attachments.MAX_BYTES):
    if not re.fullmatch(r"a_[0-9a-f]{64}", attachment_id):
        raise BridgeError("Use an attachment ID from outlook_list_attachments.")
    def write(path):
        value = attachment_request("attachment", message_id, attachment_id=attachment_id, export_path=str(path.resolve()), max_bytes=max_bytes)
        return {**value["attachment"], "account": value["account"], "source": "classic_outlook_object_model",
                "message_id": message_id, "attachment_id": attachment_id, "client": "outlook"}
    return attachments.export_original(write, max_bytes)
