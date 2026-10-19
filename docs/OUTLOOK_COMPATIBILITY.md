# Classic Outlook compatibility and CLI access

Reviewed October 19, 2026. Classic Outlook for Windows exposes the Outlook Object
Model through local Windows PowerShell 5.1/COM. Mail lookup does not require
Computer Use, screenshots, accessibility or mouse/keyboard automation.
See Microsoft's [Application API](https://learn.microsoft.com/en-us/office/vba/api/outlook.application).

Version 0.10.0 adds `outlook_diagnostics` and `outlook_start`. Diagnostics use
Windows installation/profile-presence metadata and current-session processes,
without COM activation or account/mail access. Start uses the existing App Paths
registration, requires an existing profile, leaves a running client alone and
never accepts an executable/profile/account argument. Only that explicit command
can start Outlook; search/read/status retain their existing behavior. No Outlook
process is killed. Outlook may show its normal window even when launched hidden;
the bridge does not operate it. A running process does not prove COM readiness.

The mail adapter uses [Account.DeliveryStore](https://learn.microsoft.com/en-us/office/vba/api/outlook.account.deliverystore)
and [NameSpace.GetItemFromID](https://learn.microsoft.com/en-us/office/vba/api/outlook.namespace.getitemfromid).
It attaches only to the user's running classic instance. Account/store/folder/item
scope checks remain in place before accessing mail. Existing selected-account
settings remain outside the plugin; there is no implicit account change.
Microsoft Graph, Exchange Online, a Microsoft 365 subscription and PST/OST parsing
are not needed for this adapter.

Reading some body/address properties can trigger [Object Model Guard](https://learn.microsoft.com/en-us/office/vba/outlook/how-to/security/protected-properties-and-methods).
A CLI cannot promise prompt-free access under every organization's configuration.
Busy COM calls allow one retry; timeouts/access denials ask the user to resolve
any login, profile or security prompt. The agent must not inspect/click those
windows, bypass script/Trust Center policy or change antivirus/registry security.

Supported here: classic Outlook for Windows, including Office 2019. New/web/Mac
Outlook, shared delivery stores and extra archive stores remain unsupported.
Other providers/PCs require their own checks. Outlook may synchronize normally;
local access does not prove offline operation or complete server coverage.
See [release validation](RELEASE_VALIDATION.md) for current verification evidence.
