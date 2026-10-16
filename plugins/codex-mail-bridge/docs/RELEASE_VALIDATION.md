# Mail Bridge 0.8.1 release validation

Validated October 17, 2026. This report contains technical outcomes only. No
mailbox identities, subjects, bodies, filenames, message/store IDs, user paths or
attachment contents are included. Account-specific evidence stays outside releases.

## Runtime correction

A running classic Outlook window can exist before `GetActiveObject` can resolve
its COM registration. Version 0.8.1 recovers only the missing-ROT-entry error by
connecting through Outlook's documented single-instance COM activation, after
confirming exactly one Outlook process exists in the caller's Windows session.
Closed, foreign-session or ambiguous instances are refused. Security and other COM
errors are not retried this way. No logon, profile selection or policy changes are
performed; existing account/store/folder/item checks still run before mail access.
The existing `v0.8.0` tag is preserved.

See Microsoft's [Outlook automation guidance](https://learn.microsoft.com/en-us/office/vba/outlook/concepts/getting-started/automating-outlook-from-other-office-applications).

## Checks completed

| Check | Result |
| --- | --- |
| Plugin unit/runtime suite | 94 passed; no skips in this run |
| Release/publication suite | 22 passed |
| Extracted plugin ZIP | Every file matched the inspected Git tree; CLI version/schema discovery worked |
| Live Thunderbird CLI | Status, compact metadata search, body continuation/revision hash, conversation budget, attachment metadata search/list/get passed |
| Live classic Outlook for Windows / Office 2019 CLI | The same operations and native attachment SaveAsFile export passed |
| Requested original files | Host-side byte counts and SHA-256 matched; repeated export hashes agreed; copies survived CLI exit |
| Export release | Every validation export was explicitly released |
| Outlook read-state check | Sampled body and attachment messages retained their before/after unread state |
| Separate generated PDF/DOCX handoff | Host-only libraries read the exported originals; the bridge added no document parser |
| Boundaries | Existing account choices retained; no send/save/delete/move/mark-read, forced sync, remote image fetch or security-policy changes requested |

The local CLI ran from extracted release content through Codex command/file tools.
The currently installed older plugin was not replaced during this verification.
Automatic routing in a newly installed 0.8.1 plugin conversation, other providers,
Exchange-specific SMTP resolution, other PCs and live non-Windows Thunderbird
remain unverified. Successful sampled requests do not certify complete mailbox
coverage, all attachments, or every client/store layout. No public demo recording
or OpenAI directory approval is claimed.

## Download and install

For a complete local installation, download **codex-mail-bridge-0.8.1-source.zip**
from the GitHub Release. It includes the local marketplace and plugin directory.
Extract it into a folder you intend to keep, open a terminal in that folder, then:

```powershell
codex plugin marketplace add .
codex plugin add codex-mail-bridge@cyp-soft-local
```

Reload Codex and start a new local conversation. Python 3.10+ and host command/file
access are required; Node.js is an optional launcher. Classic Outlook must already
be running and Windows PowerShell must permit scripts under the existing policy.
Private account selections are outside the package and are preserved.

The smaller **codex-mail-bridge-0.8.1-plugin.zip** contains one plugin for a host's
supported package workflow. It has no marketplace wrapper. Do not register that
directory as a marketplace without providing the host's required marketplace
configuration. Git installation is also available:

```powershell
codex plugin marketplace add Cyp9715/Codex-Mail-Bridge --ref v0.8.1
codex plugin add codex-mail-bridge@cyp-soft-local
```

Use the release SHA256SUMS file to verify downloaded ZIP bytes. GitHub Release
distribution is independent of the OpenAI public directory.
