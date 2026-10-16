"""Bound model-facing text while preserving IDs and explicit continuation."""
import hashlib
import re


def message_identity(item, client, account_scope=""):
    """Expose a duplicate candidate key, never silently discard mailbox copies."""
    header = str(item.get("message_id_header") or "").strip()
    if header.startswith("<") and header.endswith(">"):
        header = header[1:-1]
    usable = (not item.get("message_id_header_truncated") and
              bool(re.fullmatch(r"[^\s<>\x00-\x1f]{1,2048}@[^\s<>\x00-\x1f]{1,2048}", header)))
    basis = "internet_message_id" if usable else "local_message_id"
    identity = header if usable else str(item["id"])
    digest = hashlib.sha256((client + "\n" + account_scope + "\n" + basis + "\n" + identity).encode("utf-8")).hexdigest()
    item.update(dedup_key="m_" + digest, dedup_basis=basis)
    return item


def folder_page(folders, limit=50, offset=0):
    shown = []
    for folder in folders[offset:offset + limit]:
        name = str(folder.get("name") or "")
        shown.append({**folder, "name": name[:400], "name_truncated": len(name) > 400})
    more = len(folders) > offset + limit
    return {"folders": shown, "folder_count": len(folders), "folders_returned": len(shown),
            "has_more_folders": more, "next_folder_offset": offset + limit if more else None}


def bounded_metadata(item):
    clipped = []
    for key in ("subject", "from", "to", "sender", "recipients", "folder", "folder_name", "message_id_header"):
        if key in item:
            text = str(item[key] or "").replace("\x00", "")
            item[key] = text[:400]
            if len(text) > 400:
                clipped.append(key)
    if "attachment_names" in item:
        names = item["attachment_names"]
        if isinstance(names, str):
            item["attachment_names"] = names[:400]
            truncated = len(names) > 400
        else:
            item["attachment_names"] = [str(name)[:200] for name in names[:5]]
            truncated = len(names) > 5 or any(len(str(name)) > 200 for name in names)
        item["attachment_names_truncated"] = truncated or item.get("attachments_truncated", False)
        if item["attachment_names_truncated"]:
            clipped.append("attachment_names")
    item["metadata_truncated_fields"] = clipped
    return item


def body_page(body, limit, offset=0):
    text = body[offset:offset + limit]
    more = offset + len(text) < len(body)
    return {"body": text, "body_characters": len(body), "body_offset": offset,
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "body_offset_unit": "unicode_characters", "body_truncated": offset > 0 or more,
            "has_more_body": more, "next_body_offset": offset + len(text) if more else None}


def budget_bodies(messages, maximum):
    remaining = maximum
    clipped = False
    for item in messages:
        body = item.get("body", "")
        if len(body) > remaining:
            item["body"] = body[:remaining]
            item["body_truncated"] = item["has_more_body"] = True
            units = len(item["body"].encode("utf-16-le")) // 2 if item.get("body_offset_unit") == "utf16_code_units" else len(item["body"])
            item["next_body_offset"] = item.get("body_offset", 0) + units
            item["body_omitted_by_budget"] = remaining == 0
            clipped = True
        remaining -= len(item.get("body", ""))
    return {"body_characters_returned": maximum - remaining,
            "body_character_budget": maximum, "body_budget_exhausted": clipped}
