# Classic Outlook compatibility review

Reviewed October 16, 2026. The locally installed product is Office Standard 2019
Volume, x64, version 16.0.10417.20208. A running classic Outlook profile exposed
one IMAP account and one unique delivery store. Live discovery, explicit account
selection, folder/status inspection, bounded search, body reading, and conversation
reading passed. A separate before/after test confirmed the sampled message's
unread flag was unchanged. Production mail is not part of this report or package.

The design uses the supported [Outlook Account.DeliveryStore](https://learn.microsoft.com/en-us/office/vba/api/outlook.account.deliverystore)
and [NameSpace.GetItemFromID](https://learn.microsoft.com/en-us/office/vba/api/outlook.namespace.getitemfromid)
APIs. It attaches to the running Outlook instance through Windows PowerShell 5.1;
it does not require Microsoft Graph, Exchange Online, Microsoft 365 subscription,
or a guessed PST/OST path. Outlook must already be running in the user's session.

Protected body/address properties can trigger [Object Model Guard](https://learn.microsoft.com/en-us/office/vba/outlook/how-to/security/protected-properties-and-methods).
The bridge respects those prompts and organization policies. No antivirus,
Trust Center, registry policy, authentication, or script policy is weakened.
Timeouts/errors do not fall back to another account or arbitrary file reader.

Support is classic Outlook for Windows. New Outlook, web Outlook, Outlook for Mac,
additional archive stores, and shared delivery stores are outside this adapter's
scope. Other classic Office editions may expose the API but have not had live
validation here. Outlook's provider may fetch remote data; offline-only behavior
and live freshness are not promised. Read-only means the bridge performs no
mailbox mutation, not that the Outlook application itself stops synchronizing.
