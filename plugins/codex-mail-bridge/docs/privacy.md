# Privacy notice

Thunderbird Mail Bridge · Cyp · effective October 29, 2026

## Local access

Discovery reads registered Thunderbird profiles and limited account/server
preferences. It can share profile names, account addresses and server metadata
with the invoking AI host. Mail queries read the local global search index for
one explicitly chosen IMAP/POP3 account. No password stores are read.

Selected-account results can contain subjects, senders, recipients, dates, folders,
opaque message/conversation IDs, body sections and indexed filenames. Attachment
search is metadata only. Listing reads one scoped message's local MIME structure;
get decodes only the requested attachment and makes its original bytes available
as a private local file. Host file/image tools open selected originals separately.
The bridge performs no document parsing, OCR, attachment execution or image fetch.

The bridge does not send, save drafts, delete, move or mark messages read. It never
launches Thunderbird, signs in, forces sync or changes application security policy.
It makes no network mail requests. Its results cover existing local index/cache
data, which can be stale or incomplete.

Diagnostics reads executable registrations and limited profile/account
configuration, returning only aggregate counts and setup guidance. It opens no
mail database and exposes no executable/profile paths or account identities.
Installation detection and local account registration do not verify server login.

## Private storage

`thunderbird.json` outside the plugin stores opaque profile/account IDs and an
identity fingerprint. It contains no password, email address, mail or profile path.
Read-only operations may reuse older Thunderbird selection files without migrating
them. A new explicit account choice writes only the bridge's current settings.

Get creates an exact original copy at a generated private path. The default file
limit is 10 MiB, with up to 100 MiB by explicit request. The receipt includes name,
size, SHA-256, type, provenance and export ID. Up to 16 exports remain under
`exports/` in the settings directory or a local `MAIL_BRIDGE_EXPORT_ROOT` override.
Later exports or `--cleanup` remove copies older than ten minutes; unexpired files
are preserved when storage is full. An OS lock serializes export and cleanup.

`--release EXPORT_ID` removes one finished generated original and its empty
directory. Cleanup never recursively deletes arbitrary paths or follows links.
No background cleaner runs; locked files or no later cleanup can leave copies.
Switching accounts cannot recall existing exports, host copies or chat history.
See [attachment details](ATTACHMENT_SUPPORT.md).

## AI host and support

There is no Cyp backend, telemetry, analytics, advertising, payment or mail archive.
The local launcher downloads nothing and starts no server or network listener.
Local execution does not make GPT offline: retrieved mail/metadata and host-opened
files can reach OpenAI under the invoking host's settings and retention policies.
The bridge cannot delete those host/chat copies. Check organizational authorization
before processing confidential data.

GitHub hosts the project and voluntary public support issues under its own policies.
Do not include private mail, settings, paths, credentials or account identities in
issues. There is no separate support collection/retention backend.

Disable/uninstall the plugin to stop access. Delete current/legacy selection files
to forget choices; this does not erase Thunderbird mail or AI-host history.
See the [README](../README.md) for settings locations and [support](support.md).
