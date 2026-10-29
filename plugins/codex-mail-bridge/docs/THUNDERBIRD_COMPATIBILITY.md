# Thunderbird compatibility and local access

Version 0.11.0 reads existing Thunderbird data through Python's standard library.
There is no dependency on another mail application's APIs or desktop automation.
Sign in and sync needed mail in Thunderbird and allow its global search index to
finish. The bridge never starts the application or initiates synchronization.

## Profiles and account boundaries

Discovery reads registered `profiles.ini` entries and limited `prefs.js` settings.
Relative and absolute profile entries are supported. Standard Windows/macOS/Linux
registries, Linux Snap and Flatpak registries are recognized. `THUNDERBIRD_HOME`
can identify another registry. IMAP/POP3 accounts with a configured identity are
eligible; no account is implicitly selected. Discovery shares profile/account
metadata with the AI host, without reading mail or password stores.

Queries bind the chosen profile/account IDs to an identity fingerprint. Folder
URIs must match its account type, host, username and effective port. Changed or
ambiguous scope fails closed. The SQLite index opens read-only, excludes deleted
rows and cannot write mail. Conversations shared across accounts remain scoped.
Private selection files and older Thunderbird selections remain compatible.

## Index and cache limits

`global-messages-db.sqlite` supplies indexed text and filename metadata only.
Thunderbird must have global indexing enabled for the needed messages. Unindexed
mail, incomplete text, stale rows and unsynchronized folders can be absent.
Status timestamps/counts and successful searches do not establish server coverage.
There is no fallback to remote protocols, full-profile scans or client launching.

Original attachments require a safely mapped local mbox or maildir cache. The
selected server's `directory-rel`/`directory` and `storeContractID` settings locate
storage. Custom Unicode paths and normal nested `.sbd` folders are supported.
Overlapping roots, escaping/unsafe paths and layouts that cannot be mapped safely
are refused. An indexed RFC Message-ID must match the cached MIME before use.
Missing, duplicate, changed or protected identities fail closed.

Cache scan continuation, message/attachment limits, encrypted MIME and unsupported
layout handling are described in [attachment support](ATTACHMENT_SUPPORT.md).
The bridge does not download, decrypt or execute attachments. Document/image
interpretation is a separate authorized host action after original-file export.

## Validation boundary

Synthetic tests cover explicit selection, cross-account refusal, read-only SQLite,
Unicode matching/continuation, custom cache paths, mbox/maildir identity checks and
original-file export. Platform discovery code is not proof of live compatibility
on every operating system, packaging format or Thunderbird version. Installed-host
routing and complete server synchronization require separate checks.
See [candidate validation](RELEASE_VALIDATION.md).
