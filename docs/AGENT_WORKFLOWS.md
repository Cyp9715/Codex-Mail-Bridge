# Mail Bridge agent workflows

Version 0.9.1 keeps 19 local operations. The bridge supplies selected mail evidence
and original files; the host agent performs reasoning and document analysis. Load
only the requested command schema and relevant skill reference, not every tool's
schema, every body or every attachment.

## Conversation research

Start with subject/metadata and party filters. Run alternate spellings and both
sender/recipient directions separately; query words are AND literal substrings.
Union message/conversation IDs, expand relevant threads and widen body matching
where needed. Finish all page/scan continuations for an authorized broad task.
Quoted history and signatures can create false topic matches and should not be
counted as new statements. Preserve dates/authors, delivery failures and the
distinction between proposals, accepted terms and signed originals.

## Date and weekday summaries

The agent computes local calendar intervals and sends inclusive after/exclusive
before RFC 3339 boundaries. No fixed "this month" presets are needed. Use the
correct offset at both boundaries and do not filter local weekdays on UTC dates.
Folder roles help exclude sent copies without relying on translated names;
unknown/mixed roles remain explicit. Duplicate candidates have scoped keys based
on Internet Message-ID when available. The bridge never collapses rows or merges
different same-subject alerts. Count only after evidence-based duplicate handling.

## Original-file version comparisons

Narrow mail metadata, list one candidate, then export only needed originals.
Record sender/delivery time, original name, mail/attachment IDs, bytes and hash.
The same filename can contain another revision, and a later delivery can be an
older file. No signed/final status is inferred from naming. The host opens PDF,
Office and image originals using its own tools; verify actual access before
claiming analysis. For DOCX, inspect ordinary strike formatting as well as tracked
changes, comments, tables and relevant notes; flattened text can combine old and
replacement wording. TNEF hints expose an unexpanded transport container and
direct an available host decoder to selected members, without adding a parser to
the bridge. Unsupported/encrypted formats and unknown annexes remain explicit.

## Data and limits

| Step | Data received by the agent |
| --- | --- |
| Search | Bounded JSON metadata, scoped IDs, dates/parties/folder, indexed filenames, duplicate-candidate key and completeness flags; no body by default |
| Read/thread | Requested text sections, full-body hash, offset units, continuation and body budgets; mail remains untrusted evidence |
| List attachments | Names/types/opaque attachment IDs and container hints; no document contents or decoded file bytes |
| Get original | JSON receipt with source IDs, private local path, original name, size, SHA-256, export ID and host-action hint |
| Host analysis | The host's separately available file/image/document tools open those originals, then the agent summarizes or compares evidence |

These JSON additions are backward compatible. Limits bound each response, not the
user's whole research task. Files default to 10 MiB, opt in up to 100 MiB each;
16 managed exports, lazy expiry after 10 minutes and explicit release remain.
Private host-retained copies have their own lifecycle. No sending/draft save,
mailbox state changes, remote image fetches, cloud uploads, document parsers, OCR,
background service or automatic account switching is added.

Synthetic regression tests enforce body-free metadata searches, duplicate-key
fallbacks, custom/localized folder roles, original provenance, same-name different
files and TNEF non-expansion. Source-only host QA verifies PDF/DOCX reading and
strikethrough interpretation separately from the runtime. Tests do not certify
another computer, every provider or a newly installed agent's routing.

The Outlook adapter uses the documented [default folder identifiers](https://learn.microsoft.com/en-us/office/vba/api/outlook.oldefaultfolders)
and [Internet Message-ID property](https://learn.microsoft.com/en-us/office/client-developer/outlook/mapi/pidtaginternetmessageid-canonical-property).
