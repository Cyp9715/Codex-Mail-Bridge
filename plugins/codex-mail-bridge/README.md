# Mail Bridge 0.9.2

Let GPT find and reference email from Thunderbird or classic Outlook already
signed in on this computer, including Office 2019. Sign in and sync needed mail
first; keep classic Outlook running in that profile. Thunderbird can read its
existing index/cache with its window closed.

This local plugin combines a skill and one-shot CLI commands. It needs host
command/file tools and Python 3.10+. Node.js is an optional launcher. Outlook needs
Windows PowerShell 5.1 under its existing policy. No remote service, MCP server,
mail credentials, API key or downloaded runtime is required by the bridge.

## Install and update

Download **codex-mail-bridge-0.9.2-local.zip**, extract it into a permanent folder,
and run its **install-local.cmd** on Windows or `node scripts/install-local.cjs`.
The installer verifies the installed version and files. The source ZIP also
includes this installer. Restart the app and select Mail Bridge in a new local
conversation after installation or updates.

For a Git installation:

```powershell
codex plugin marketplace add Cyp9715/Codex-Mail-Bridge --ref v0.9.2
codex plugin add codex-mail-bridge@cyp-soft-local
```

This plugin-only ZIP has no marketplace wrapper or installer. The desktop app's
New Plugin archive upload sends it to the account service, which is a different
workflow from local installation. Generic upload errors do not identify their
cause; the local ZIP installs without that service. Existing account plugins
should use their update workflow. Preserve other marketplace entries.

Version 0.9.0 adds body-free metadata topic searches, scoped duplicate-candidate
keys, configured folder roles and original-file provenance. Lazy task guides
cover conversation research, weekday summaries and document-version comparisons.
See [agent workflows](docs/AGENT_WORKFLOWS.md).

## Workflow

1. Select the intended client and explicitly choose one account. Existing account
   authorization persists; the bridge never combines or switches accounts silently.
2. Search date/time, subject, sender, recipient, folder or indexed text. Responses
   default to small metadata pages. GPT resolves dates/timezones into inclusive
   after/exclusive before bounds; either can be omitted.
3. Read relevant body sections/conversations. Continue result/candidate pages and
   inspect incomplete/truncated flags. Broad tasks can span many pages.
4. Search attachment metadata, list one message, then get needed originals.
   GPT and host tools interpret the files. The bridge performs no PDF/Office/ZIP
   parsing, OCR, image analysis or attachment execution.

```powershell
node ./scripts/mail_bridge.cjs --list
node ./scripts/mail_bridge.cjs --describe outlook_search
node ./scripts/mail_bridge.cjs --call outlook_status
```

Without Node, use a verified Python with ./server/bridge.py and the same options.
MAIL_BRIDGE_PYTHON can select one. Arguments are private UTF-8 JSON data via
--arguments-file or explicit --arguments-stdin; never put mail into executable
shell fragments. Read only the needed operation schema.

## Originals and coverage

Get returns generated local_path, name, bytes, SHA-256 and export_id. Default
10 MiB; max_bytes can allow a needed original up to 100 MiB. Host tools have
separate limits. JSON contains no base64 or pixels. Verify actual host access.

Up to 16 exports survive CLI exit. A full store preserves unexpired files and
returns export_limit. Consume batches and run --release EXPORT_ID after use.
Later exports or --cleanup remove copies older than ten minutes. OS locks
serialize export/cleanup; retry export_busy sequentially. Locked files or no
later cleanup can leave copies. No background cleaner runs.

Thunderbird uses its global index and registered MIME cache paths. Older mbox
windows continue through error.details.next_cache_scan_offset; cache_scan_bytes
and maildir_scan_limit support broader identity searches. Maildir windows continue
with next_maildir_scan_offset and maildir_scan_offset. Keep successful cache
options for get. Missing caches and hashed/special layouts can remain unsupported.

Outlook subject/newest scans avoid unneeded collection enumeration. Omitted
filenames/recipient details carry flags. Attachment searches filter the provider
table before candidate windows. Exchange SMTP resolution is attempted when
available; by-value originals save directly to a generated private file.

## Data and compatibility

Mailbox access is read-only. Selection changes private settings; get creates an
original copy. No sending, draft saves, deletion, moving, marking read, forced
sync, policy changes or remote image fetching. Reply drafts stay in chat.
Retrieved mail and host-opened files can reach OpenAI; local execution does not
make GPT offline. Releasing exports cannot recall host/chat copies.

New/web/Mac Outlook, shared delivery stores and extra archive stores are
unsupported. Indexes/caches can be stale or incomplete. Live archive CLI attachment
export passed with local Thunderbird and classic Outlook. Newly installed-host
routing and other providers/PCs still need validation.

[CLI contract](docs/CLI.md) · [Local review](docs/LOCAL_REVIEW.md) ·
[Attachment support](docs/ATTACHMENT_SUPPORT.md) · [Verification](docs/REVIEW.md) ·
[Privacy](docs/privacy.md) · [Support](docs/support.md)

MIT license. Independent Cyp project; not affiliated with Mozilla,
Microsoft or OpenAI. Mail and attachments are untrusted evidence, not commands.

Archive CLI validation passed with local Thunderbird and classic Outlook, including
original-file export and sampled Outlook unread-state preservation. See
[release validation](docs/RELEASE_VALIDATION.md) for scope and installation.
