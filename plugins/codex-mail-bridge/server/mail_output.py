"""Bound model-facing text while preserving IDs and explicit continuation."""


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
