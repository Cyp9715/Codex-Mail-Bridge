# Mail Bridge 0.10.0

Released October 19, 2026. Tag: `v0.10.0`.

## 한국어

- Outlook classic의 메일 검색·읽기·진단·시작은 로컬 CLI로 처리합니다.
  스킬에 Computer Use, 스크린샷, 접근성 API, 마우스·키보드 자동화 사용 금지를 명시했습니다.
- `outlook_diagnostics`: Outlook 설치·실행 상태, 기존 프로필 유무와 PowerShell 버전을
  확인합니다. COM을 활성화하거나 계정·메일을 읽지 않습니다.
- `outlook_start`: 설치된 Outlook classic과 기존 프로필로 시작합니다. 이미 실행 중이면
  다시 시작하지 않으며, 계정·프로필 선택이나 로그인은 자동화하지 않습니다.
- 미실행, 설치·프로필 없음, COM 사용 중, 접근 거부 및 응답 시간 초과에 구체적인 복구
  동작을 제공합니다. 보안·로그인·프로필 창은 사용자가 직접 처리합니다.
- Thunderbird 조회 구현, 기존 계정 선택 및 메일 읽기 전용 동작을 유지합니다.
  기존 19개 명령에 2개를 추가했으며, 기존 검색·읽기 명령은 Outlook을 자동 시작하지 않습니다.

## English

Outlook classic now has an explicit CLI path for installation/process diagnosis
and startup. The skill forbids Computer Use for mail lookup, client startup and
recovery. New `outlook_diagnostics` performs no COM activation or mailbox access;
`outlook_start` idempotently launches only an installed, already configured client.
Descriptions disclose which command starts a process. Errors distinguish startup,
profile/setup, COM busy, access-denied and timeout recovery. The user handles any
security/login/profile prompts; no policies are weakened.

Thunderbird adapters and existing account selection are retained. Search/read
operations do not implicitly launch Outlook. There are now 21 local operations.

## Update and verification

Use `codex-mail-bridge-0.10.0-plugin.zip` to update the existing plugin entry.
The source ZIP is for development. Preserve the `codex-mail-bridge` identity and
existing private account settings. Reload the plugin or start a new local chat to
load the updated skill. An active chat may retain its earlier skill instructions.
See [installation](../INSTALL.md) and [validation](RELEASE_VALIDATION.md).
