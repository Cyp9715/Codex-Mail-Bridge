# Thunderbird design review

The source has one mail retrieval path: a registered Thunderbird profile and one
explicitly selected IMAP/POP3 account. Profile preferences establish scope; a
read-only SQLite connection supplies indexed metadata/text; the scoped mbox/maildir
adapter supplies selected original bytes. The optional Node.js launcher discovers
an existing Python and exits after one operation.

## Boundaries

- Discovery reads only registered profiles and limited account preferences, without
  mail contents, password stores or exposed filesystem paths.
- Selection persists opaque IDs and an identity fingerprint outside the plugin.
  Existing authorized Thunderbird selections and deduplication keys stay stable.
- Queries filter every message by account folder URI and nondeleted index state.
  Threads cannot cross the selected account even if the index shares conversation IDs.
- Metadata search avoids body reads by default. Body continuation uses Unicode
  character offsets and full-body hashes; thread budgets preserve IDs/continuation.
- Attachment list/get verifies cache storage scope and matching RFC Message-ID.
  Ambiguous identities, unsafe layouts and protected MIME fail closed.
- Original export uses generated paths, bounded bytes, hashes, OS locks and explicit
  release/lazy expiry. Mailbox data and client/security settings remain untouched.

The CLI exposes exactly ten Thunderbird operations. Direct attachment registration
keeps schemas and callable signatures aligned. Both manifests share identity,
version, presentation and local-executor requirements. Runtime inventory checks
reject stale modules from overlay upgrades, and installed module bytes are verified.

## Limits

The local index is not a server-completeness oracle. Indexed dates are not separate
receipt timestamps. Configured folder roles do not establish direction for every
message. Body hashes identify textual revisions; duplicate keys identify candidates
without silently collapsing mailbox copies. Host file access, document interpretation
and AI retention remain separate from original-file transfer.

Synthetic fixtures verify the boundaries without production mail. Live platform
compatibility, installed-host routing and complete server sync need separate
evidence. See [validation](RELEASE_VALIDATION.md) and
[publication controls](DEVELOPMENT_SECURITY.md).
