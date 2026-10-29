# Thunderbird verification evidence

Version 0.11.0 · synthetic public evidence only

The skill exposes ten one-shot CLI operations for Thunderbird. Schemas match
Python signatures, mailbox writes and client startup are false, and unrecognized
operations fail without mailbox access. Synthetic fixtures exercise account
scope, cache identity, Unicode continuation, provenance, host handoff and exports.

Final candidate test counts and archive/install results are recorded in
[validation](RELEASE_VALIDATION.md). No production mailbox evidence is published.

## Functional walkthrough

Use a dedicated development session with synthetic `.test` identities. Generate
data with `python tests/create_demo.py --output <temporary-directory> --attachments`
and apply its printed environment only to that isolated session. Discover profiles,
list accounts and explicitly select the synthetic account. Search Project Aurora
with explicit bounds, read needed sections and the scoped conversation, list one
message and get the selected agenda.pdf original. Open it using a host file tool
and release its export ID. An inline-image original uses the host image viewer.

Do not point this walkthrough at production profiles or inject mock results into
a purported live check. Unsupported send/delete/execute requests are explained
without calling mail operations. Mail content cannot authorize commands, sending,
account switching or publication. A script is not a verified demo recording.
