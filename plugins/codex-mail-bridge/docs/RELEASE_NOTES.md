# Mail Bridge 0.10.0

Released October 19, 2026. Tag: `v0.10.0`.

## Changes

- **CLI-only Outlook workflows.** Mail search, reading, diagnostics and startup
  use local CLI commands. The skill explicitly forbids Computer Use, screenshots,
  accessibility APIs, and mouse or keyboard automation for mail tasks and recovery.
- **Mail-free diagnostics.** `outlook_diagnostics` checks installation and process
  state, existing-profile presence and the Windows PowerShell version. It does not
  activate COM or access account identities or mail.
- **Explicit, idempotent startup.** `outlook_start` launches installed classic
  Outlook with an existing configured profile. It leaves an already running
  instance alone and does not automate account/profile selection or login.
  Command descriptions disclose which operation starts the client.
- **Actionable recovery.** Errors distinguish a stopped client, missing
  installation/profile, COM busy, access denial and timeouts. The user handles
  security, login and profile prompts; no security policies are weakened.
- **Existing behavior preserved.** Thunderbird adapters, existing account choices
  and read-only mailbox access are retained. Two runtime commands bring the total
  from 19 to 21 local operations. Existing search/read commands do not implicitly
  start Outlook.

## Update and verification

Use `codex-mail-bridge-0.10.0-plugin.zip` to update the existing plugin entry.
The source ZIP is for development. Preserve the `codex-mail-bridge` identity and
existing private account settings. Reload the plugin or start a new local chat to
load the updated skill. An active chat may retain its earlier skill instructions.
See [installation](../INSTALL.md) and [validation](RELEASE_VALIDATION.md).
