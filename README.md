# Mail Bridge for Codex

[한국어 안내](README.ko.md)

<img src="plugins/codex-mail-bridge/assets/icon.png" alt="Mail Bridge icon" width="96">

**A Cyp Soft desktop plugin for reading Thunderbird and classic Microsoft Outlook
mail in Codex. Office 2019 is supported; a Microsoft 365 subscription is not required.**

Mail Bridge provides read-only mailbox access: search, read, and summarize mail,
follow conversations, and compose reply text in chat. It cannot create, send,
save, delete, move, or mark mail as read. Reply text stays in chat until you use
your mail client yourself. Only the bridge's private account-choice settings are written.

The MIT-licensed source contains no real mail, account settings, passwords, PST/OST,
Thunderbird index, or personal computer paths. Retrieved account metadata and mail
are returned to the AI host; local execution does not make the AI service offline.

## Supported clients

| Client | Access method | Requirements and verified scope |
| --- | --- | --- |
| Thunderbird | Registered profiles and local global search index | IMAP/POP3; Windows integration tested. macOS/Linux discovery has synthetic tests, not real-machine certification. |
| Classic Outlook for Windows | Running Outlook's COM Object Model and the selected account's delivery store | Office Standard 2019 x64 tested. No Microsoft 365 subscription or Microsoft Graph connection is needed. |
| New Outlook, Outlook on the web, Outlook for Mac | Not implemented | These do not use this adapter's classic Windows COM workflow. |

Classic Outlook installed through another Office edition may expose the same API,
but only the Office 2019 environment above has live evidence. This project does
not replace OpenAI's cloud Outlook connector or claim that connector supports
perpetual Office installations. See [compatibility evidence](docs/OUTLOOK_COMPATIBILITY.md).

## Installation

Use a local Codex desktop session with plugin support, Node.js 18+ on PATH, and
Python 3.10+. The launcher uses an existing Python; it downloads nothing.
`MAIL_BRIDGE_PYTHON` can select an executable. The former `THUNDERBIRD_PYTHON`
override remains compatible. Outlook also needs Windows PowerShell 5.1 and a
running classic Outlook profile. The bridge does not bypass script or Outlook policies.

```powershell
git clone https://github.com/Cyp9715/Codex-Mail-Bridge.git
cd Codex-Mail-Bridge
codex plugin marketplace add .
codex plugin add codex-mail-bridge@cyp-soft-local
```

Reload the desktop app if tools are not visible. Specify your client, for example:
“Show my classic Outlook accounts and help me connect one,” or “Help me select
one Thunderbird account.” An explicit choice is required even if an account is
the default. If the client is ambiguous, the agent should ask before accessing mail.

The package lives in `plugins/codex-mail-bridge/`. Use the source ZIP for the local
marketplace, or the plugin-only ZIP through a host's supported package workflow.
For a previous local installation, remove its old identifier before installing
the new one; private selection settings are outside the package:

```powershell
codex plugin remove thunderbird-bridge@cyp-soft-local
codex plugin add codex-mail-bridge@cyp-soft-local
```

The older 0.1.x installation identifier was `thunderbird-mail-bridge`.

## Tools and limits

- Thunderbird: `thunderbird_profiles`, `thunderbird_accounts`,
  `thunderbird_select_account`, `thunderbird_status`, `thunderbird_search`,
  `thunderbird_read`, `thunderbird_thread`.
- Outlook: `outlook_accounts`, `outlook_select_account`, `outlook_status`,
  `outlook_search`, `outlook_read`, `outlook_thread`.

Each client has one explicitly selected account. Selecting Outlook does not
switch the Thunderbird choice, and a combined search is never implicit.
Search supports literal keywords, sender, recipient, folder, and UTC date range.
`after` includes its UTC date; `before` excludes its UTC date.

Thunderbird results are local indexed text and may omit unsynced or unindexed mail.
Outlook results come from the selected account's unique delivery store. Additional
archive stores, virtual search folders, Deleted Items, Drafts, and Outbox are excluded.
Accounts sharing one delivery store are rejected because account isolation would
be ambiguous. Folder and item IDs are checked before reading message content.

Outlook scans the newest 1,000 candidates by default, with a maximum of 5,000 and
a time budget. `scan_incomplete` indicates partial coverage; pagination applies
within that scan window. Keyword body search examines at most 6,000 characters
per message. Body/recipient/attachment-name truncation is disclosed. Empty search
results never prove absence from the full mailbox. Conversations may be partial
outside the scan window. Outlook addresses may be legacy Exchange addresses.

Attachment names are available; attachment contents are not. There are no
send, compose-window, draft-save, delete, move, read-state change, forced-sync,
security-policy change, or arbitrary PowerShell/SQL execution tools. Outlook's
own configured provider may retrieve data over the network; offline access and
live server freshness are not guaranteed. Security prompts require the user's
normal Outlook controls; the bridge never disables Object Model Guard.

Attached images, inline CID images, PDFs, Word and Excel contents are not readable
in 0.3.0. The [attachment feasibility review](docs/ATTACHMENT_SUPPORT.md) describes
the Outlook API extension and optional Thunderbird companion needed to add them.
These are planned capabilities, not installed tools.

## Portable discovery and private settings

No fixed mail path or publisher account is assumed. Thunderbird profiles are
discovered from `profiles.ini`, including registered absolute/nonstandard profile
paths. Standard Windows/macOS/Linux, Snap, and Flatpak registries are supported.
`THUNDERBIRD_HOME` can identify another registry directory. Outlook discovers
accounts and delivery stores through its running profile API; PST/OST paths are
never guessed, parsed, or hardcoded. A different Outlook profile requires a fresh
explicit selection. See [portability and test coverage](docs/PORTABILITY.md).

Default settings directory:

- Windows: `%LOCALAPPDATA%/CypSoft/MailBridge/`
- macOS: `~/Library/Application Support/CypSoft/MailBridge/` (Thunderbird)
- Linux: `$XDG_CONFIG_HOME/CypSoft/MailBridge/`, or `~/.config/CypSoft/MailBridge/` (Thunderbird)

`thunderbird.json` and `outlook.json` contain opaque account/profile identifiers
and identity fingerprints, never addresses, passwords, mail, or absolute profile
paths. `MAIL_BRIDGE_THUNDERBIRD_SETTINGS` and `MAIL_BRIDGE_OUTLOOK_SETTINGS` can
select independent per-client settings files. The older Thunderbird settings
override remains supported. Override paths are local environment configuration,
never tool arguments supplied by the model.

If a new Thunderbird file is absent, the bridge can read prior
`CypSoft/ThunderbirdBridge/settings.json` or `CypSoft/ThunderbirdMailBridge/settings.json`.
Read-only calls do not move files. A new explicit selection writes the new location.
Invalid new settings do not fall back to a previous account. Overrides never fall
back to other files. Remove the plugin to stop access; delete current and previous
selection files to forget choices. This does not erase mail or AI-host history.

## Tests and review data

```powershell
python -m unittest discover -s plugins/codex-mail-bridge/tests -p "test_*.py"
python plugins/codex-mail-bridge/tests/create_demo.py --output ./work/review-demo
python scripts/package.py --output ./outputs
```

The demo generator uses only reserved `.test` addresses and fake Thunderbird
mail. Outlook unit tests use synthetic objects; they are not a recording of real
Outlook. See [review walkthrough](plugins/codex-mail-bridge/docs/REVIEW.md) and
[submission preparation](docs/SUBMISSION.md). Public recordings must use isolated
test data, never production mail.

## Distribution and support

Contributors must follow the [publication controls](docs/DEVELOPMENT_SECURITY.md).
Local checks cover staged files, commit messages, historical content, and release
inputs; account-specific protected strings stay in an ignored private denylist.

This is a private/local development plugin with MIT source distribution.
OpenAI public directory submission is separate. As checked October 16, 2026,
[local MCP submissions require an approved organization](https://developers.openai.com/plugins/deploy/desktop-only).
Publisher verification and a verified, reviewer-accessible recording remain open.
No approval, submission, or public directory publication is claimed.

[Support](docs/support.md) · [Privacy](docs/privacy.md) · [Terms](docs/terms.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

Mail Bridge is an independent Cyp Soft project, not an official or endorsed
Mozilla, Thunderbird, Microsoft, or OpenAI product. Product names describe
interoperability; no third-party logos or trademark permissions are claimed.
