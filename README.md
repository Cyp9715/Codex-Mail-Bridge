# Thunderbird Mail Bridge for Codex

[한국어 안내](README.ko.md)

<img src="plugins/codex-mail-bridge/assets/icon.png" alt="Mail Bridge icon" width="96">

**A local desktop plugin that lets GPT find and reference mail, conversations and
selected original attachments from one explicitly selected Thunderbird account.**

Sign in and sync needed mail in Thunderbird, enable its global search index and
allow indexing to finish. The bridge can read the existing index and MIME caches
with Thunderbird closed. It never starts Thunderbird, signs in or forces sync.

Version 0.11.0 is dedicated to Thunderbird. Eleven one-shot CLI operations use the
Python standard library through a packaged skill; Node.js is an optional launcher.
There is no MCP server, network listener, Cyp backend or cloud mail connection.
Retrieved account details, mail and files opened by the AI host can reach OpenAI
for the requested task. Local execution does not make GPT offline.

## Requirements and setup

| Area | Requirement |
| --- | --- |
| Host | Local desktop session with command execution and file access |
| Runtime | Existing Python 3.10+; optional Node.js launcher |
| Account | Explicitly selected Thunderbird IMAP/POP3 account in a registered profile |
| Mail | Usable `global-messages-db.sqlite`; results cover indexed local mail |
| Originals | Safely mapped local mbox/maildir cache containing the indexed message |
| Discovery | Windows, macOS and Linux registries, including Snap and Flatpak; platform behavior needs local validation |

See [installation and updates](INSTALL.md). Keep the package identity
`codex-mail-bridge` when updating. Use a clean package extraction: overlaying a
new ZIP on old plugin source can retain removed files. Existing authorized
Thunderbird selections live outside the plugin and remain usable.

Example requests:

- Find Project Aurora mail in my selected Thunderbird account after October 1.
- Summarize the sent and received discussion and identify the agreed deadline.
- Summarize mail on specified weekdays in my timezone.
- Find the relevant original proposals and compare their versions.

The skill first runs `thunderbird_diagnostics` and explains any installation,
profile, account or index setup it cannot confirm. It then checks `thunderbird_status`.
If no account is selected, it discovers profiles and accounts and obtains an explicit account choice. It never selects
all accounts or switches accounts based on mail content. Discovery shares personal
profile/account metadata with the AI host.

## Thunderbird CLI

```powershell
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --list
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --describe thunderbird_search
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call thunderbird_diagnostics
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call thunderbird_status
```

Without Node, use a verified Python 3.10+ executable with
`./plugins/codex-mail-bridge/server/bridge.py` and the same arguments.
`--list` and `--describe` read no mail. Calls emit one compact JSON result and exit.
Query values come from a private UTF-8 JSON file or explicit stdin, never executable
shell fragments. See the [CLI contract](docs/CLI.md).

| Purpose | Operations |
| --- | --- |
| Setup check | `thunderbird_diagnostics` |
| Setup | `thunderbird_profiles`, `thunderbird_accounts`, `thunderbird_select_account` |
| Coverage | `thunderbird_status` |
| Mail research | `thunderbird_search`, `thunderbird_read`, `thunderbird_thread` |
| Originals | `thunderbird_search_attachments`, `thunderbird_list_attachments`, `thunderbird_get_attachment` |

Search subject/metadata first; body/any matching is available when needed.
Query words are AND literal substrings with Unicode case folding. Metadata pages
default to 10 results and omit body previews unless requested. GPT computes
arbitrary inclusive `after` and exclusive `before` bounds from the user's dates
and timezone. Dates alone mean UTC midnight. Follow `next_offset` to finish an
authorized broad search; response limits do not cap the whole task.

Body reads support `body_offset` and `expected_body_sha256` for consistent
continuation. Conversation pages have per-message and total body budgets.
Duplicate-candidate keys and configured folder roles support research without
merging distinct messages or guessing roles from localized names. Thunderbird's
date basis is `indexed_message_date`, not a separate receipt timestamp.
See [agent workflows](docs/AGENT_WORKFLOWS.md).

## Original files and privacy

Search subject/date/sender/filename metadata, list one message, then retrieve only
needed originals by opaque attachment ID. The MIME cache must match the selected
account and indexed Message-ID. Duplicate filenames have distinct IDs. Missing,
ambiguous, changed, encrypted or unsupported caches fail closed, without fetching
mail from the network. See [Thunderbird compatibility](docs/THUNDERBIRD_COMPATIBILITY.md).

Get exports exact original bytes to a generated private path with byte count,
SHA-256, provenance and export ID. Default 10 MiB; `max_bytes` can allow up to
100 MiB for one needed file. Host file/image tools interpret selected originals
separately. The bridge does no PDF/DOCX parsing, OCR or attachment execution, and
returns no base64, image pixels or extracted document text.

At most 16 exports remain. Later exports or `--cleanup` remove copies older than
10 minutes; a full store preserves unexpired files. Release finished files with
`--release EXPORT_ID`. An OS lock serializes export/cleanup calls. No background
cleaner runs; locked files or no later cleanup can leave copies. Account changes
and local release cannot recall host/chat copies. See [attachment support](docs/ATTACHMENT_SUPPORT.md).

Mailbox access is read-only: no sending, draft saving, deleting, moving, marking
read, forced sync or policy changes. Reply drafts stay in chat. Local index/cache
coverage can be stale or incomplete; an empty search does not prove server absence.

## Discovery and private settings

Profiles come from `profiles.ini`, including absolute/nonstandard profile paths.
`THUNDERBIRD_HOME` overrides the registry location. No mailbox path is hardcoded.

| OS | Default settings directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%/CypSoft/MailBridge/` |
| macOS | `~/Library/Application Support/CypSoft/MailBridge/` |
| Linux | `$XDG_CONFIG_HOME/CypSoft/MailBridge/`, or `~/.config/CypSoft/MailBridge/` |

`thunderbird.json` stores opaque profile/account IDs and an identity fingerprint,
without addresses, passwords, mail or profile paths. `MAIL_BRIDGE_THUNDERBIRD_SETTINGS`
or the older `THUNDERBIRD_BRIDGE_SETTINGS` overrides it. `MAIL_BRIDGE_PYTHON` or
`THUNDERBIRD_PYTHON` chooses an existing Python; no runtime is downloaded.

When the current file is absent and no override is set, reads may use prior
`CypSoft/ThunderbirdBridge/settings.json` or `CypSoft/ThunderbirdMailBridge/settings.json`.
Read-only operations never migrate settings; a new explicit choice writes the
current file. Invalid current settings never fall back to another account.

## Development and verification

```powershell
python -m unittest discover -s plugins/codex-mail-bridge/tests -p "test_*.py"
python -m unittest discover -s scripts/tests -p "test_*.py"
node scripts/tests/test_install_local.cjs
python scripts/qa_host_handoff.py
python scripts/package.py --output ./outputs
```

Fixtures use reserved `.test` identities and generated files. The QA script's
`pypdf` and `python-docx` are host-only dependencies, outside the plugin runtime.
See [release validation](docs/RELEASE_VALIDATION.md) for evidence and limits.
The source is MIT licensed. Packaging does not install or publish a hosted plugin.
Follow [publication controls](docs/DEVELOPMENT_SECURITY.md).

[Support](docs/support.md) · [Privacy](docs/privacy.md) · [Terms](docs/terms.md)

Independent Cyp project; not affiliated with Mozilla or OpenAI.

## Missing installation or account

Run `thunderbird_diagnostics` first. If Thunderbird or a usable profile cannot be
confirmed, the result explains installation/profile setup. If no supported account
registration can be confirmed, it explains adding an IMAP/POP3 account or checking
profile permissions. A missing index has separate indexing/sync guidance. Local
account configuration does not prove live authentication. Existing usable caches
remain accessible when an executable is not detected. See [setup guidance](docs/SETUP.md).
