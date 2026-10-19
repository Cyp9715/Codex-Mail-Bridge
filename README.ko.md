# Mail Bridge

[English](README.md)

**이 컴퓨터에 로그인된 Thunderbird 또는 클래식 Outlook의 메일을 GPT가
찾아보고 참조하도록 돕는 데스크톱 전용 플러그인입니다. Office 2019도 지원합니다.**

사용 전에 메일 클라이언트에서 로그인하고 필요한 메일을 동기화하세요.
클래식 Outlook은 로그인된 프로필로 실행 중이어야 합니다. Thunderbird는
창이 닫혀 있어도 기존 로컬 색인과 캐시를 읽을 수 있습니다.
플러그인이 로그인하거나 암호를 요청하지 않습니다.

현재 버전은 **0.10.0**이며 패키지 개발자 표기는 **Cyp**입니다.

## 동작 방식

0.7.0부터 MCP 서버 없이 **스킬과 로컬 스크립트**로 동작합니다.
GPT가 필요한 조회 명령을 실행하고 작은 JSON 결과를 참조합니다.
별도의 원격 서버, 네트워크 수신 포트, Cyp의 백엔드는 없습니다.
조회한 계정 정보와 메일 본문, 호스트에서 연 파일은 요청 처리를 위해
OpenAI에 전달될 수 있습니다. 로컬 실행이 GPT의 오프라인 처리를 뜻하지 않습니다.

- 명령 실행과 파일 읽기가 허용된 **로컬 데스크톱 대화**가 필요합니다.
  웹·모바일·클라우드 전용 대화에서는 PC의 메일함에 접근할 수 없습니다.
- Python 3.10+가 필요합니다. 선택적인 Node.js 실행기는 설치된 Python을 찾으며
  런타임이나 의존성을 다운로드하지 않습니다.
- Outlook은 Windows, 클래식 Outlook 및 Windows PowerShell 5.1이 필요합니다.
  기존 스크립트 실행 정책과 Outlook 보안 정책을 그대로 따릅니다.
- 새 Outlook, 웹 Outlook, Mac용 Outlook과 공유 배달 저장소는 지원하지 않습니다.

## Outlook classic의 CLI 사용

0.10.0은 Outlook 실행 상태 확인과 시작까지 CLI로 처리합니다. 메일 조회에
Computer Use, 스크린샷, 마우스·키보드 자동화는 필요하지 않습니다.

```powershell
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call outlook_diagnostics
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call outlook_start
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call outlook_status
```

진단은 COM을 활성화하거나 계정·메일을 읽지 않습니다. Outlook 시작은 설치된
실행 파일과 기존 프로필을 이용하며, 이미 실행 중이면 그대로 둡니다.
기존 검색·읽기 명령은 Outlook을 자동 실행하지 않습니다. 로그인·프로필 선택·보안
경고가 필요하면 사용자가 직접 처리해야 하며, 에이전트가 화면 조작으로 우회하지
않습니다. Outlook 자체 창이 표시될 수는 있으나 플러그인은 창을 조작하지 않습니다.
Thunderbird 조회 구현과 기존 계정 선택은 유지됩니다.
[릴리스 노트](docs/RELEASE_NOTES.md)를 참고하세요.

## 메일 조회와 파일 참조

사용자가 고른 클라이언트의 계정 하나만 명시적으로 선택합니다.
허락 없이 계정을 바꾸거나 여러 계정을 합쳐 조회하지 않습니다.
기존에 선택한 계정과 설정은 유지됩니다.

기간 시작·종료, 제목, 본문, 발신자, 수신자, 폴더, 첨부파일 이름으로 검색할 수
있습니다. GPT가 사용자의 날짜 표현과 시간대를 해석하고 명시적인
`after`/`before` 값으로 조회합니다. 시작은 포함, 종료는 제외이며 어느 쪽이든
생략할 수 있습니다. 날짜 또는 시간대 오프셋이 있는 RFC 3339 시각을 받습니다.

검색은 기본적으로 작은 메타데이터 페이지를 반환합니다. `field:"metadata"`는
제목·발신자·수신자·파일명만 검색하며 본문을 읽지 않습니다. 중복 식별 키는 후보를
구분하는 정보이며, 플러그인이 메일을 자동으로 합치지는 않습니다. 필요한 본문 구간과
대화만 추가로 읽습니다. 넓은 조회는 페이지, Outlook 후보 구간, 기간·폴더 분할로
이어갈 수 있습니다. 작은 기본값이 사용자 작업 전체의 범위를 제한하지 않습니다.
불완전한 검색, 잘린 본문, 오래된 색인 여부를 GPT에 명시합니다.

첨부파일은 이름·제목·기간 등으로 후보를 좁힌 뒤 한 메일의 목록을 확인하고,
필요한 **원본 파일만** 전달합니다. PDF·Word·Excel 내용을 플러그인에서 파싱하지
않으며, 호스트의 파일 도구가 읽도록 원본 경로와 크기·SHA-256을 제공합니다.
메일 속 이미지도 원본으로 전달하고 필요할 때 호스트 이미지 도구로 봅니다.
Base64나 이미지 픽셀을 JSON 응답에 넣지 않습니다. 호스트가 실제로 파일을
읽었는지는 전달 성공과 별도로 확인해야 합니다.

원본은 기본 10 MiB이며, 필요한 파일은 `max_bytes`로 최대 100 MiB까지 허용할 수 있습니다.
최대 16개를 비공개 로컬 export 경로에 보관합니다.
짧은 명령 프로세스가 끝나도 읽을 수 있으며, 사용 후 export ID로 정리합니다.
10분 경과 후 다음 export나 명시적 정리에서 삭제합니다. 보관 한도가 차면
아직 만료되지 않은 파일을 지우지 않고 사용 완료 파일의 정리를 요청합니다.
잠긴 파일이나 이후 정리가 실행되지 않은 파일은 남을 수 있습니다.

메일 발송·초안 저장·삭제·이동·읽음 변경·강제 동기화·보안 설정 변경은 하지
않습니다. 답장 초안은 채팅에만 작성합니다. 계정 선택은 플러그인 자체 설정을,
첨부파일 조회는 선택한 원본의 임시 사본만 기록합니다.

## 설치와 업데이트

GitHub Release에서 **codex-mail-bridge-0.10.0-plugin.zip**을 받으세요.
처음 추가할 때는 데스크톱 앱의 **새 플러그인** 창에서 ZIP을 그대로 선택합니다.
등록 후 Mail Bridge 화면에 **플러그인 설치**가 표시되면 설치하고,
새 로컬 대화에서 Mail Bridge를 선택하세요. 별도 설치 프로그램은 필요하지 않습니다.

**이미 같은 이름의 플러그인이 있다면 새로 생성하지 말고 기존 항목을 업데이트하세요.**
보고된 0.9.1 추가 오류는 사용자가 기존 동일 이름 플러그인과의 충돌로 확인했습니다.
기존 항목에 제공되는 업데이트·새 버전 업로드 기능을 사용하고, 패키지 이름
`codex-mail-bridge`는 유지하세요. 업데이트 기능이 없어 교체해야 한다면 기존
항목 삭제에 앞서 패키지와 공유 범위를 확인해야 합니다. [설치 안내](INSTALL.md)를 참고하세요.

ZIP의 두 manifest와 About 설명은 개발자를 **Cyp**로 명시합니다.
계정에 등록된 플러그인의 개발자 표기는 호스트 서버가 별도로 제공할 수 있으며,
ZIP의 작성자명을 수정해도 업로드 계정의 이름이나 신원이 변경되지는 않습니다.
소스 ZIP과 Git 마켓플레이스는 개발자를 위한 선택 사항으로 유지합니다.

0.9.0은 본문을 읽지 않는 메타데이터 검색, 중복 후보 식별, 폴더 용도, 원본 출처
정보와 대화·요일별 정리·문서 버전 비교 안내를 보강했습니다. Thunderbird의 오래된 mbox는 `cache_scan_offset`으로 이어서
찾고 `cache_scan_bytes`로 탐색 범위를 넓힐 수 있습니다. Maildir도
`maildir_scan_offset`으로 이어서 찾고 `maildir_scan_limit`을 조절할 수 있습니다.

```powershell
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --list
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --describe outlook_search
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call outlook_status
```

Node가 없다면 확인된 Python으로 `server/bridge.py`에 동일한 옵션을 전달할 수
있습니다. 필요한 명령의 스키마만 조회하고, 조건은 비공개 UTF-8 JSON 데이터
파일로 전달합니다. [CLI 규약](docs/CLI.md)을 참고하세요.

0.10.0 검증은 137개가 통과했고 기존 스크립트 정책으로 PowerShell 검사 1개를 건너뛰었습니다.
ZIP 구조·파일 일치와 격리된 로컬 설치·업데이트·원본 전달도 검증했습니다.
계정 ZIP 업로드와 자동 스킬 호출은 로컬 CLI 검증과 구분합니다.
0.9.0 배포 ZIP의 CLI로 실제 Thunderbird와 클래식 Outlook의
검색·본문 이어 읽기·대화·첨부 원본 전달을 확인했고, 표본 Outlook 메일의 읽음 상태도 유지됐습니다.
실행 중인 Outlook의 COM 연결 보완도 유지합니다. 다른 PC·공급자와 새 설치본의
자동 스킬 호출 검증은 남아 있습니다. [검증 범위와 ZIP 설치 안내](docs/RELEASE_VALIDATION.md)를 참고하세요.
소스는 MIT 라이선스이며 공개 디렉터리의 승인과 별개입니다.

현재 버전은 로컬 Git 마켓플레이스와 ZIP 배포에 집중합니다.
OpenAI 공개 제출 포털 없이 로컬 설치할 수 있습니다.
[에이전트 활용과 데이터 형식](docs/AGENT_WORKFLOWS.md) 및 [로컬 설계 검토](docs/LOCAL_REVIEW.md)에 개선 내용과 남은 검증 범위를 기록했습니다.

[지원](docs/support.md) · [개인정보](docs/privacy.md) · [이용약관](docs/terms.md)

Mozilla·Microsoft·OpenAI와 제휴하지 않은 Cyp의 독립 프로젝트입니다.
