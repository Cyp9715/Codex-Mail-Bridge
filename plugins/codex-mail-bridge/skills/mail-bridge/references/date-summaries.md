# Summarize date-selected mail

GPT computes calendar dates; the bridge accepts arbitrary explicit time bounds.
Resolve the year and timezone from the user's context. State a reasonable
assumption when unambiguous; ask only when alternatives materially change the
answer. Treat each day as local midnight inclusive to the next midnight exclusive
with the correct UTC offset on each boundary, including daylight-saving changes.

For a month plus weekday request, enumerate the matching calendar days locally
and search each interval, or search the bounded month and filter converted dates.
Never apply weekday tests to UTC dates when the user means local days. Days still
in the future are pending, not completed days with no mail.

Search Thunderbird metadata without snippets first and finish matching pages.
For "received mail", exclude identified sent folders using
status role / message folder_role, not English or translated display names.
The role other does not prove a message was received or sent: report unresolved
scope or inspect the relevant sender/folder evidence. Keep received self-copies
when present in the inbox. Thunderbird date_basis is indexed_message_date;
do not claim it provides an independent receipt timestamp.

Retain mailbox rows until duplicate candidates are checked. Identical
internet_message_id dedup keys can connect inbox/label copies in one selected
account, but compare relevant evidence before counting one. Missing/invalid
headers use local_message_id and remain separate; explicitly label uncertain
counts rather than silently merging by date/subject/sender. Different messages
with identical subjects, including security alerts, must remain distinct.

Read a short body section for each distinct relevant message, then continue only
as needed. Group the summary by local day/time and identify action requests,
notifications and newsletters. Summarize newsletter claims as the email's claims;
do not imply independent fact checking. Do not reproduce authentication codes,
magic links, reset tokens or unrelated personal details. State whether spam,
archives or unknown-role folders were included, counts after confirmed duplicate
handling and any partial search/sync limits. No message is marked read.
