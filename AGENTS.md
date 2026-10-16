# Repository instructions

This is public source for a local mail bridge. Production mailbox data must never
be published. Use synthetic `.test` identities and generated documents/images for
examples, fixtures, screenshots, tests, logs, issues, PR descriptions and commit
messages. Never copy real subjects, bodies, attachment names/contents, account or
server identities, store/message IDs, private settings, credentials or user paths
into any publication, including diagnostic comments.

Read `docs/DEVELOPMENT_SECURITY.md` before publication and
`docs/ATTACHMENT_SUPPORT.md` before work on attachment support. Local protected
strings belong only in the ignored private denylist; do not repeat them here or
send them as GitHub search queries. Perform authorized mailbox comparisons locally
and keep account-specific audit reports under ignored `work/` or `private/` paths.

Before a GitHub blob/commit/ref write, including connector/API writes that bypass
Git hooks, stage the exact intended files and check the complete staged tree,
history and exact proposed message with `scripts/run_publication_guard.cjs`.
Do not bypass failed checks or remove private rules to force a pass. Commit messages
describe general technical behavior only. Check the saved remote tree against the
inspected tree and preserve an expected-parent/ref lease when publishing updates.

Run the tests affected by changes, plus release validation when packaging changes.
Respect explicit per-client account selection and mailbox read-only behavior.
No fixed mail/profile paths, unsolicited client/account switching, remote image
fetches, mail security-policy changes, or attachment execution. Clearly distinguish
planned attachment capabilities from implemented and tested runtime tools.

For each versioned release, synchronize the portable manifest, compatibility
manifest and MCP server versions, then create and push an immutable `v<version>`
tag at that release commit. Preserve existing version tags.
