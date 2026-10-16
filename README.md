# Mail Bridge for Codex

[한국어 안내](README.ko.md)

<img src="plugins/codex-mail-bridge/assets/icon.png" alt="Mail Bridge icon" width="96">

**A desktop plugin that lets GPT find and reference mail from Thunderbird or
classic Outlook already signed in on this computer, including Office 2019.**

**Sign in to your desktop mail client and sync the mail you need before use.
Keep classic Outlook running in that signed-in profile.** Thunderbird can read
an existing local index/cache with its window closed. The bridge does not log in
or request passwords.

Version 0.9.0 uses a **skill and one-shot local scripts**. No MCP server, network
listener, Cyp Soft backend or cloud mail connection is needed. The installed
skill invokes only the requested local operation and receives compact JSON.
Retrieved account details, mail text and files opened by the AI host can be sent
to OpenAI for the requested task. Local access does not mean offline GPT processing.

## Supported environment

| Area | Requirement |
| --- | --- |
| Host | Local desktop conversation with permission to execute commands and read files; web/mobile and cloud-only sessions cannot access the desktop mailbox |
| Runtime | Existing Python 3.10+; optional Node.js launcher discovers a runtime without downloads |
| Thunderbird | Signed-in IMAP/POP3 account, registered profile and existing local global index; selected original files also need a safely mapped MIME cache |
| Classic Outlook | Running Windows classic Outlook profile, including Office 2019, and Windows PowerShell 5.1 with its existing script policy |
| Host file analysis | Authorized host document/image tools; exporting a file does not establish that GPT has read it |

New Outlook, web Outlook and Outlook for Mac are unsupported. Shared Outlook
delivery stores and additional archive stores are rejected. Local indexes/caches
may be incomplete or stale; Outlook's own provider may fetch data normally.
The bridge does not force sync or weaken client or script security policies.

## Local installation and use

Install `plugins/codex-mail-bridge` using the host's supported local marketplace
flow. This repository includes `.agents/plugins/marketplace.json`; preserve other
marketplace entries. Start a new local conversation after installation/reload and
select Mail Bridge. To register this Git marketplace:

```powershell
codex plugin marketplace add Cyp9715/Codex-Mail-Bridge --ref v0.9.0
```

Choose the Cyp Soft local marketplace in the host plugin browser and install Mail Bridge. Reload the installed plugin after updates; editing source does not rewrite installed caches.

Ask for the intended client/account, such as:

- Find Project Aurora mail in my selected Thunderbird account after October 1.
- Read the relevant classic Outlook conversation and summarize the decisions.
- Find the requested PDF by sender and date, then read only that original file.

The skill checks the account's status and obtains an explicit account choice when
needed. It never silently selects all accounts, combines clients or switches
accounts. Existing authorized selections are preserved. Discovery itself returns
personal profile/account metadata to the AI host.

There are 19 local operations. Each schema is available on demand, without reading
mail or loading every schema into the conversation:

```powershell
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --list
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --describe outlook_search
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call outlook_status
```

If Node is unavailable, run `python ./plugins/codex-mail-bridge/server/bridge.py`
with the same arguments using a verified Python 3.10+ interpreter. Query values
are JSON data from stdin or a private UTF-8 argument file, never executable shell
fragments. See the [CLI contract](docs/CLI.md).

## Targeted queries and broad review

Version 0.9.0 adds body-free metadata topic searches, scoped duplicate-candidate
keys, configured folder roles and original-file provenance. Lazy task guides
cover conversation research, weekday summaries and document-version comparisons.
See [agent workflows](docs/AGENT_WORKFLOWS.md).

| Caller control | Behavior |
| --- | --- |
| after / before | Arbitrary inclusive start and exclusive end; either can be omitted; RFC 3339 timestamps with Z/offset or UTC dates |
| query / field / sender / recipient / folder_id | Literal selected-account filters |
| filename | Attachment metadata filter; no document contents are opened to search filenames |
| limit / offset | Bounded result pages; defaults limit each response, not the whole user task |
| folder_limit / folder_offset | Status folder pages while retaining account-wide counts |
| scan_limit / scan_offset | Outlook candidate windows and continuation; partition by date/folder for wider coverage |
| body_search_limit | Outlook local body matching depth without returning matching bodies |
| max_characters / body_offset / expected_body_sha256 | Targeted body sections with optional revision consistency |
| max_characters_per_message / max_total_characters | Per-message and aggregate conversation body budgets |
| max_bytes | Original-file limit, default 10 MiB; caller may raise to 100 MiB |
| cache_scan_bytes / cache_scan_offset / maildir_scan_limit / maildir_scan_offset | Thunderbird cache identity search windows and broader scans |
| include_snippet | Optional body previews; off by default |

GPT resolves relative dates, language and timezone conventions. The bridge exposes
explicit bounds instead of language-specific presets. Search returns metadata by
default; `search_incomplete`, `scan_incomplete`, matching truncation and
`coverage_scope` must be considered even when no matches are returned. Pagination
and date/folder partitions support authorized broad work. Empty local results do
not establish absence from the server mailbox.

## Selected original attachments and images

Search subject/date/sender/filename metadata, list one candidate message, then get
only the relevant original attachment by its opaque ID. Duplicate filenames are
distinct IDs. Original files default to 10 MiB; `max_bytes` can allow up to
100 MiB for a needed larger file. They are exported unchanged to generated local
paths with byte counts, SHA-256 and export IDs. PDF/Office documents remain files
for the host's authorized tools. Inline images are viewed through the host's image
tool only when needed. The CLI emits no base64, image pixels or document text.

The bridge has no PDF/Office parsers, OCR, attachment execution, cloud upload API
or implicit bulk transfer. User-requested broad review can retrieve multiple
relevant originals in manageable batches. Verify host access before claiming
that GPT read a document.

Exports survive the short CLI process so the host can read them. They are stored
under the private application-data settings directory, at most 16 files, with a
10-minute lazy expiry on later exports or explicit `--cleanup`. A full store
returns `export_limit` and preserves unexpired files. OS file locking serializes
export and cleanup across processes. Release each file
with `--release <export_id>` after analysis. Locked files or no later cleanup can
leave copies. Account changes cannot recall existing host/chat copies.
See [attachment support](docs/ATTACHMENT_SUPPORT.md).

Mailbox access stays read-only: no sending, compose windows, draft saves, deletion,
moving, read-state changes, forced sync, policy changes or arbitrary SQL/PowerShell.
Reply drafts remain in chat. Account selection writes only private bridge settings;
attachment retrieval writes selected original copies outside the plugin.

## Portable discovery and private settings

Thunderbird uses registered `profiles.ini` paths, including absolute/nonstandard
profiles; standard Windows/macOS/Linux, Snap and Flatpak registries are recognized.
`THUNDERBIRD_HOME` can identify another registry. Outlook uses its running profile's
account and delivery-store API; it does not guess or parse PST/OST paths.

| OS | Default settings directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%/CypSoft/MailBridge/` |
| macOS | `~/Library/Application Support/CypSoft/MailBridge/` (Thunderbird) |
| Linux | `$XDG_CONFIG_HOME/CypSoft/MailBridge/`, or `~/.config/CypSoft/MailBridge/` (Thunderbird) |

`thunderbird.json` and `outlook.json` store opaque selection IDs/fingerprints, not
addresses, passwords, mail or profile paths. `MAIL_BRIDGE_THUNDERBIRD_SETTINGS`
and `MAIL_BRIDGE_OUTLOOK_SETTINGS` override each independently. The older
`THUNDERBIRD_BRIDGE_SETTINGS` override remains supported. Runtime overrides are
local environment configuration, not mail-operation arguments.

Without an explicit override, an absent new Thunderbird setting can read prior
`CypSoft/ThunderbirdBridge/settings.json` or `CypSoft/ThunderbirdMailBridge/settings.json`.
Reads do not migrate files; a new explicit choice writes the current location.
Invalid current settings do not silently fall back to another account. Disable or
uninstall the plugin to stop access; delete current/legacy settings to forget
choices. This does not erase client mail or AI-host history.

## Verification and distribution

```powershell
python -m unittest discover -s plugins/codex-mail-bridge/tests -p "test_*.py"
python -m unittest discover -s scripts/tests -p "test_*.py"
python scripts/qa_host_handoff.py
python scripts/package.py --output ./outputs
```

Tests and fixtures use reserved `.test` identities and generated files. The QA
script's `pypdf`/`python-docx` are separate host-only test dependencies; runtime
uses the Python standard library and existing Windows COM adapter. See
[verification evidence](plugins/codex-mail-bridge/docs/REVIEW.md). Live native
Archive CLI status/search/read/thread and original-file export passed live
Thunderbird and classic Outlook checks, including sampled Outlook unread-state
preservation. Installed-host routing and other providers/PCs remain unverified.
See the [release validation and ZIP installation guide](docs/RELEASE_VALIDATION.md).

The source is MIT licensed and distributed as a local Git marketplace and ZIP.
The OpenAI public submission portal is not required for local installation.
See the [local design review](docs/LOCAL_REVIEW.md) for findings, decisions and
remaining compatibility checks. Historical directory notes are in
[submission status](docs/SUBMISSION.md).

[Support](docs/support.md) · [Privacy](docs/privacy.md) · [Terms](docs/terms.md)

Independent Cyp Soft project; not affiliated with Mozilla, Microsoft or OpenAI.
Contributors must follow [publication controls](docs/DEVELOPMENT_SECURITY.md).
