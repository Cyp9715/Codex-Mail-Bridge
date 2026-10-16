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
Attachment searches use metadata only. An explicitly requested attachment get
reads one original file and makes it available to the host as a private temporary
local file; supported images also return typed image content. No document parsing
or OCR is performed. The bridge does not read password stores or create, send,
save, delete, move, or mark mail as read.

## Local storage and network

Private per-client settings hold opaque account/profile IDs and identity
fingerprints outside the plugin. They contain no passwords, addresses, mail,
or absolute profile paths. Read-only calls may read previous-version selections
but never migrate or modify settings. A new explicit selection writes only the
bridge's own settings. Delete current and legacy files to forget selections.

Attachment get creates a random OS-temporary directory and generated filename
containing the exact original bytes, up to 10 MiB. The host receives the path,
name, size, hash and resource URI. Exports are limited to 16; after 10 minutes,
later transfer/resource requests attempt cleanup, as does normal process exit.
Crashes, locked files or no later request can leave copies. Remove only the
returned files and their generated empty directories when finished. No server
mail archive is maintained. Switching accounts does not recall host copies or
already exported files. See [attachment details](ATTACHMENT_SUPPORT.md).

There is no Cyp Soft backend, analytics, telemetry, advertising, payment, or
mail archive. The launcher downloads nothing. The Python/PowerShell bridge
does not directly call a network mail service, but Outlook's configured provider
may fetch data or synchronize as part of its normal client operation. No forced
sync or security-policy change is implemented. Offline operation is not guaranteed.

## AI host and GitHub

Local execution does not make the AI service offline. Retrieved metadata and
mail, requested originals and images are made available to the invoking AI host
under its own settings, storage, and
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
