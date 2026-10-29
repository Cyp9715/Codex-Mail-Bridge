# Thunderbird Mail Bridge

Find and reference mail, conversations and selected original attachments from one
explicitly chosen Thunderbird account. Version 0.11.0 provides ten one-shot local
CLI operations through a skill. Python 3.10+ and local command/file access are
required; Node.js is an optional launcher. No MCP server or remote mail service
is needed. See [installation and updates](INSTALL.md).

Sign in and sync needed mail in Thunderbird and allow global indexing to finish.
The bridge reads an existing `global-messages-db.sqlite` and scoped local mbox or
maildir MIME caches, even with Thunderbird closed. It never launches a mail client,
logs in, forces sync or changes mailbox data. Discovery covers registered profiles
on Windows/macOS/Linux, with local compatibility validation still required.

```powershell
node ./scripts/mail_bridge.cjs --list
node ./scripts/mail_bridge.cjs --describe thunderbird_search
node ./scripts/mail_bridge.cjs --call thunderbird_status
```

Without Node, use a verified Python executable with `./server/bridge.py` and the
same arguments. `--list` and `--describe` read no mail. Private JSON input files or
explicit stdin carry arguments as data. See the [CLI contract](docs/CLI.md).

| Purpose | Operations |
| --- | --- |
| Setup | `thunderbird_profiles`, `thunderbird_accounts`, `thunderbird_select_account` |
| Coverage | `thunderbird_status` |
| Research | `thunderbird_search`, `thunderbird_read`, `thunderbird_thread` |
| Originals | `thunderbird_search_attachments`, `thunderbird_list_attachments`, `thunderbird_get_attachment` |

Start with subject/metadata searches. Paginate results, read needed body sections
and expand relevant conversations within the selected account. Explicit time
bounds, duplicate-candidate keys, configured folder roles and body hashes support
date summaries and conversation research. See [workflows](docs/AGENT_WORKFLOWS.md).

Attachment search uses indexed filenames only. List one candidate and export only
needed originals by opaque ID. The local MIME Message-ID must match the indexed
message within its selected account. Missing/ambiguous caches fail closed without
network fetching. Returned path, bytes, SHA-256 and provenance support host file
analysis; the bridge does no document parsing, OCR or execution.

Originals default to 10 MiB and can explicitly allow 100 MiB. Up to 16 exports
survive CLI exit. Release finished files with `--release EXPORT_ID`; later exports
or `--cleanup` remove copies older than ten minutes. No background cleaner runs,
and local cleanup cannot recall host/chat copies. See [attachments](docs/ATTACHMENT_SUPPORT.md).

Mailbox access is read-only. Account selection writes private settings; get writes
an original copy outside the package. Local index/cache results can be stale or
incomplete. Retrieved account details, mail and files opened by the AI host can
reach OpenAI; local execution does not make GPT offline.

[Validation](docs/RELEASE_VALIDATION.md) · [Compatibility](docs/THUNDERBIRD_COMPATIBILITY.md) ·
[Support](docs/support.md) · [Privacy](docs/privacy.md) · [Terms](docs/terms.md)

Independent Cyp project; not affiliated with Mozilla or OpenAI. MIT licensed.
