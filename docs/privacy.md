# Privacy notice

Mail Bridge · Cyp Soft · effective October 16, 2026

## Local access

Thunderbird discovery reads registered profiles and limited account/server
preferences; mail queries read its local global search index. Outlook discovery
uses the running classic Windows Outlook profile's account and delivery-store
API. It never guesses or parses PST/OST files. One account per client must be
explicitly selected. Shared Outlook delivery stores are rejected.

Discovery can return profile/account names, addresses, and client metadata to
the AI host. Selected-account queries can return subjects, senders, recipients,
dates, folder names/IDs, message/conversation IDs, body text, and attachment names.
The bridge does not read password stores or attachment contents and does not
create, send, save, delete, move, or mark mail as read.

## Local storage and network

Private per-client settings hold opaque account/profile IDs and identity
fingerprints outside the plugin. They contain no passwords, addresses, mail,
or absolute profile paths. Read-only calls may read previous-version selections
but never migrate or modify settings. A new explicit selection writes only the
bridge's own settings. Delete current and legacy files to forget selections.

There is no Cyp Soft backend, analytics, telemetry, advertising, payment, or
mail archive. The launcher downloads nothing. The Python/PowerShell bridge
does not directly call a network mail service, but Outlook's configured provider
may fetch data or synchronize as part of its normal client operation. No forced
sync or security-policy change is implemented. Offline operation is not guaranteed.

## AI host and GitHub

Local execution does not make the AI service offline. Retrieved metadata and
mail are sent to the invoking AI host under its own settings, storage, and
retention policies. The bridge cannot delete host chat history. Check host
policies and organizational authorization before processing confidential mail.

GitHub hosts this project under its own policies. Voluntary support issues are
public. Do not include private mail or settings. There is no separate support
collection/retention backend.

## Stop access

Disable/uninstall the plugin and delete its current/legacy selection files to
forget account choices. This does not erase Thunderbird/Outlook data or AI-host
history. Use each application's own controls for those records.
See the [README](../README.md) for settings locations and [support](support.md)
for privacy questions, keeping private information out of public issues.
