# Distribution and submission scope

Thunderbird Mail Bridge 0.11.0 is a local desktop skill/CLI plugin. The portable
manifest uses Agent Plugins 1.0; the Codex compatibility manifest mirrors identity,
version and presentation. Both declare local execution. There is no MCP configuration,
remote endpoint, app binding, lifecycle hook or hidden server process.

The plugin ZIP contains one self-contained plugin; the source ZIP adds repository
tests, publication checks and optional local marketplace helpers. The existing
package identity and Cyp attribution are preserved. Do not create a second hosted
plugin merely to update its source.

No public-directory submission, account-hosted update or release publication is
performed by the packager. Validate current eligibility and host-specific update
requirements through the supported service before a separate submission. A valid
archive and local tests do not establish directory approval or installed-host routing.
Do not invent a remote endpoint or hide the local-executor requirement.

See [installation](../INSTALL.md), [release validation](RELEASE_VALIDATION.md)
and [publication controls](DEVELOPMENT_SECURITY.md).
