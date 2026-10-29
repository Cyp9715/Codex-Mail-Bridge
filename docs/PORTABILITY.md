# Thunderbird portability

| Boundary | Behavior |
| --- | --- |
| Runtime | Python 3.10+ standard library; optional existing Node.js launcher |
| Discovery | Registered Windows/macOS/Linux profiles, plus Linux Snap/Flatpak registries |
| Profile paths | `profiles.ini` relative/absolute paths; optional `THUNDERBIRD_HOME` |
| Account scope | Explicit IMAP/POP3 profile/account choice and unchanged identity fingerprint |
| Mail source | Read-only local global search index; no remote protocols |
| Originals | Scoped mbox/maildir caches from server storage preferences |
| Selection | Private opaque IDs/fingerprint outside the plugin; older Thunderbird selections readable |
| Exports | Generated private storage and cross-process OS locks; explicit release/lazy expiry |

`MAIL_BRIDGE_THUNDERBIRD_SETTINGS` and legacy `THUNDERBIRD_BRIDGE_SETTINGS` override
the selection path. `MAIL_BRIDGE_EXPORT_ROOT` overrides private export storage.
`MAIL_BRIDGE_PYTHON` or `THUNDERBIRD_PYTHON` chooses an existing interpreter. No
runtime downloads, hardcoded profile paths or password-store access occur.

Windows uses `%LOCALAPPDATA%/CypSoft/MailBridge/`; macOS uses
`~/Library/Application Support/CypSoft/MailBridge/`; Linux uses
`$XDG_CONFIG_HOME/CypSoft/MailBridge/` or `~/.config/CypSoft/MailBridge/`.
Settings contain no address, password, mail or absolute profile path.

Registered-profile discovery support is not evidence of live compatibility on
every operating system or Thunderbird version. Custom cache layouts can be
unsupported; missing or ambiguous identity fails closed. Installed-host routing,
another PC and complete server coverage require separate validation.
See [compatibility](THUNDERBIRD_COMPATIBILITY.md) and [validation](RELEASE_VALIDATION.md).
