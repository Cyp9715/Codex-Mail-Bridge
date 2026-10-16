# Thunderbird Bridge

[한국어 안내](README.ko.md)

<img src="plugins/thunderbird-bridge/assets/icon.png" alt="Thunderbird Bridge icon" width="96">

An independent Cyp Soft desktop plugin that connects one explicitly selected
Thunderbird mailbox to Codex through a local MCP server. MIT licensed.

The distributable contains no mailbox, account address, server name, credentials,
or personal computer path. Each person discovers and selects their own account
after installation. Selection settings stay outside the plugin package.

## Features

- Discover Thunderbird profiles and IMAP/POP3 account identities.
- Explicitly choose one account; access remains scoped to it.
- Search keywords, sender, recipient, folder, and UTC date range.
- Read indexed bodies and conversations; compose reply text in chat.
- No publisher server, telemetry, passwords, or mailbox writes.

Retrieved account metadata and mail text are passed to the AI host. Local tool
execution does not mean the AI processes the email offline.

## Requirements and installation

Use a local Codex/ChatGPT desktop session with plugin support, Node.js 18+, and
Python 3.10+. The launcher can use an existing Codex bundled Python or an installed
Python; it downloads nothing. Set `THUNDERBIRD_PYTHON` to a Python executable if
automatic discovery fails. Thunderbird Global Search and Indexer must be enabled.

Clone this repository and install its local marketplace:

```powershell
git clone https://github.com/Cyp9715/Thunderbird-Bridge.git
cd Thunderbird-Bridge
codex plugin marketplace add .
codex plugin add thunderbird-bridge@cyp-soft-local
```

If the plugin's tools do not appear immediately, reload the desktop app and start
a local chat. Ask: “Help me choose one Thunderbird account.” Select your own
account when asked, then request a search or summary. There is no server login.

The generic plugin package is in `plugins/thunderbird-bridge/`. A plugin-only
ZIP has no marketplace wrapper; for manual marketplace distribution use this
repository's source ZIP instead.

### Upgrading from 0.1.x

The installation identifier, MCP connection, and skill are now `thunderbird-bridge`.
Remove the previous local installation, then install the renamed plugin from the
updated marketplace:

```powershell
codex plugin remove thunderbird-mail-bridge@cyp-soft-local
codex plugin add thunderbird-bridge@cyp-soft-local
```

The saved account choice stays outside the plugin. If the new settings file is
absent, the bridge can read the previous `CypSoft/ThunderbirdMailBridge/settings.json`
location. Read-only calls leave both locations untouched; a new explicit account
selection writes to `CypSoft/ThunderbirdBridge/settings.json`. An existing invalid
new file does not fall back to the previous account. A settings override isolates
its specified file and never falls back to another location.

Windows installation has been tested. macOS and Linux standard, Snap, and Flatpak
profile discovery is implemented but needs testing on those operating systems.
Firefox/Thunderbird profile formats or index schemas may change; the reader
fails rather than bypassing account scope when selection no longer matches.

## Limits

The source is Thunderbird's local global search index, not the live mail server.
Some mail may be absent or stale until Thunderbird syncs and indexes it. Date
filters use UTC midnight, with inclusive `after` and exclusive `before`.
Attachment names are available, attachment contents are not. Local folders that
are not part of the selected IMAP/POP3 account are outside this version's scope.
No send, delete, move, read-status changes, or Thunderbird draft-save operations
are implemented.

## Local selection storage

- Windows: `%LOCALAPPDATA%/CypSoft/ThunderbirdBridge/settings.json`
- macOS: `~/Library/Application Support/CypSoft/ThunderbirdBridge/settings.json`
- Linux: `$XDG_CONFIG_HOME/CypSoft/ThunderbirdBridge/settings.json`, normally
  `~/.config/CypSoft/ThunderbirdBridge/settings.json`

Settings contain profile/account IDs and an identity fingerprint, not passwords,
mail contents, addresses, or absolute profile paths. Do not distribute settings.
For complete removal of the account choice, delete the current settings file and
any previous 0.1.x selection file described above.
`THUNDERBIRD_HOME` can select a nonstandard Thunderbird registry directory;
`THUNDERBIRD_BRIDGE_SETTINGS` can isolate a test settings file. Neither is a
model-provided filesystem path.

## Tests and synthetic review data

```powershell
python plugins/thunderbird-bridge/tests/test_bridge.py
python plugins/thunderbird-bridge/tests/create_demo.py --output ./work/review-demo
```

The second command creates only reserved `.test` addresses and fake mail. Set the
two printed environment variables in a dedicated demo session, discover its
profile, and explicitly select `demo@example.test`. Never use production email
in public recordings. See the packaged review walkthrough.

## Distribution state

Private local installation and MIT source distribution are supported. Public
OpenAI directory submission is a separate process. At the time of preparation,
OpenAI limits local MCP submissions to approved partner organizations.
Publisher verification, published policy/support pages, an accessible recorded
demo, and portal checks remain separate from package validation. Do not describe
this development bundle as an approved public listing.

This project is not affiliated with Thunderbird, Mozilla, or OpenAI.

## Support, privacy, and trademarks

[Support](docs/support.md) · [Privacy notice](docs/privacy.md) · [Terms](docs/terms.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

Thunderbird is a trademark of the Mozilla Foundation in the U.S. and other countries.
Cyp Soft and Thunderbird Bridge are not affiliated with, endorsed by, or sponsored
by Mozilla, Thunderbird, or OpenAI. MIT does not grant third-party trademark rights.

The installation identifier is `thunderbird-bridge`. Account discovery also returns profile names,
email addresses, and server metadata to the AI host.
