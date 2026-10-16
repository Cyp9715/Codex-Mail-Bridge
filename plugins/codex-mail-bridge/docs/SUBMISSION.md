# OpenAI directory preparation

Mail Bridge · Cyp Soft · version 0.7.0

## Package path

The plugin is now **skills only, Desktop only**: a packaged skill invokes a
one-shot local CLI against Thunderbird or running classic Outlook. The ZIP has
no `mcp.json`, `.mcp.json`, `.app.json`, `mcpServers` declaration, lifecycle hook,
network listener or hidden MCP launch. It honestly declares
`extensions.com.openai.requires_local_executor:true`; the compatibility manifest
has the same requirement. Local execution is necessary to access this PC's mail.

This follows the official [plugins without an MCP server](https://developers.openai.com/plugins/deploy/desktop-only)
path. No MCP URL, server domain verification or MCP connection setup applies to
this package. Skills-only plugins do not require MCP review cases, MCP demo or
MCP reviewer credentials. Prior MCP review cases remain in versioned Git history;
unrun cases are not represented as current live evidence.

The directory still requires applicable metadata, developer verification, skills
scans, legal attestations and review. Skills-only plugins may have additional
eligibility requirements. If `requires_local_executor` itself is rejected, ask
the OpenAI representative to confirm the submitting organization's access.
Do not remove the flag, hide local behavior, invent a remote endpoint or claim
that this source change guarantees admission. See the
[guidelines](https://developers.openai.com/plugins/plugin-guidelines).

## Prepared source and ZIP

Portable and compatibility identities are synchronized at 0.7.0. The About text
states the purpose: GPT references mail from a **locally signed-in Thunderbird or
classic Outlook account**, with Office 2019 support and no Microsoft 365 requirement.
It covers local-session/runtime prerequisites, account choice, targeted and broad
queries, original-file delivery, AI data flow and limitations. English/Korean
listing, independent icon, free/no commerce, all available countries, support,
privacy and terms URLs are retained. The developer name displayed by the portal
is determined by its selected verified identity.

## Portal handoff

1. Select the intended organization and verified developer identity.
2. Upload the **0.7.0 plugin ZIP** as a new package version of the existing draft.
   The source ZIP is for developers. No online upload is performed by packaging.
3. Confirm the saved About, version and Desktop only restriction. Inspect the saved
   draft for stale MCP/app bindings; a previous 0.6.0 draft can retain server state.
   Do not assume an updated ZIP removed portal-owned bindings. Resolve remaining
   connection findings through the supported portal flow or OpenAI support.
4. Review metadata/skill scans. If local-executor eligibility is rejected, request
   confirmation of access from OpenAI. A clean ZIP does not override account policy.
5. Verify an installed local desktop workflow before claiming host compatibility.
   Have the authorized developer complete attestations and submit for review.
   Approval and publication are separate actions.

Local CLI and synthetic file/adapter tests are evidence for the code, not a proof
of directory approval or installed-host operation. Native Outlook attachment and
another-PC testing remain pending. See [verification evidence](REVIEW.md).
