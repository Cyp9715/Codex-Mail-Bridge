# Thunderbird Mail Bridge for Codex

[English](README.md)

**이 컴퓨터의 Thunderbird 계정 하나를 명시적으로 선택해 메일·대화·원본 첨부를
GPT가 찾아 참고하도록 하는 로컬 데스크톱 플러그인입니다.**

0.11.0은 Thunderbird 전용입니다. 기존 전역 검색 인덱스와 로컬 MIME 캐시를
읽는 CLI 명령 11개로 구성됩니다. 먼저 Thunderbird에서 로그인하고 필요한 메일을
동기화한 뒤 전역 검색 인덱싱이 끝나도록 기다리세요. 인덱스와 캐시가 있으면
Thunderbird 창을 닫아도 조회할 수 있습니다. 브리지가 로그인하거나 앱을 실행하고
동기화를 강제하지는 않습니다.

## 준비와 설치

- 명령 실행과 파일 읽기가 가능한 로컬 데스크톱 세션이 필요합니다.
- Python 3.10 이상이 필요하며 Node.js 실행기는 선택 사항입니다.
- 등록된 Thunderbird 프로필의 IMAP/POP3 계정을 하나 선택합니다.
- 메일 검색은 `global-messages-db.sqlite`, 원본 첨부는 해당 계정의 로컬
  mbox/maildir 캐시가 필요합니다.
- Windows·macOS·Linux와 Snap·Flatpak 프로필 등록 위치를 탐색합니다.
  다른 운영체제와 프로필 구성의 실제 호환성은 개별 확인이 필요합니다.

[설치·업데이트 안내](INSTALL.md)를 따르세요. 패키지 이름은 `codex-mail-bridge`를
유지합니다. 이전 소스 위에 압축을 덮어 풀면 삭제된 파일이 남을 수 있으므로,
깨끗한 위치에 풀어 플러그인 디렉터리를 교체하세요. 기존에 승인한 Thunderbird
계정 선택은 패키지 외부의 개인 설정에 보관되므로 재사용할 수 있습니다.

사용 예:

- 선택한 Thunderbird 계정에서 10월 이후 Project Aurora 관련 메일을 찾아줘.
- 보낸 메일과 받은 메일을 함께 검토해서 합의된 마감일을 정리해줘.
- 내 시간대의 지정한 요일에 해당하는 메일을 요약해줘.
- 관련 제안서 원본을 찾아 버전별 변경 사항을 비교해줘.

계정이 선택되지 않았다면 프로필과 계정을 확인하고 사용자의 명시적 선택을
받습니다. 메일 내용만 보고 계정을 바꾸거나 모든 계정을 함께 검색하지 않습니다.

## CLI와 조회 흐름

```powershell
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --list
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --describe thunderbird_search
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call thunderbird_diagnostics
node ./plugins/codex-mail-bridge/scripts/mail_bridge.cjs --call thunderbird_status
```

Node.js 없이도 검증된 Python으로 `server/bridge.py`에 같은 인자를 전달할 수
있습니다. `--list`와 `--describe`는 메일을 읽지 않습니다. 입력값은 비공개 UTF-8
JSON 파일이나 명시적 stdin으로 전달하며 메일 내용을 실행 명령에 삽입하지 않습니다.

| 용도 | 명령 |
| --- | --- |
| 설치·계정 진단 | `thunderbird_diagnostics` |
| 초기 설정 | `thunderbird_profiles`, `thunderbird_accounts`, `thunderbird_select_account` |
| 선택 계정·인덱스 확인 | `thunderbird_status` |
| 메일·대화 | `thunderbird_search`, `thunderbird_read`, `thunderbird_thread` |
| 원본 첨부 | `thunderbird_search_attachments`, `thunderbird_list_attachments`, `thunderbird_get_attachment` |

제목·메타데이터를 먼저 검색하고 필요할 때 본문까지 넓힙니다. 검색어의 모든
단어가 부분 문자열로 일치해야 합니다. GPT가 날짜와 시간대를 계산해 시작 포함
`after`, 끝 제외 `before`를 전달합니다. 날짜만 쓰면 UTC 자정입니다. 결과 페이지와
본문 이어 읽기를 끝까지 확인해야 넓은 요청을 충족할 수 있습니다. Thunderbird의
날짜는 인덱스에 기록된 메시지 날짜이며 별도 수신 시각을 보장하지 않습니다.

첨부 검색은 파일명 메타데이터만 조회합니다. 후보 메일 하나의 첨부 목록을 확인한
뒤 필요한 원본만 가져옵니다. 선택 계정·메시지 식별 정보와 캐시가 일치해야 합니다.
캐시가 없거나 모호하면 실패하며 네트워크에서 대신 내려받지 않습니다.

원본은 기본 10 MiB, 명시적 요청 시 최대 100 MiB까지 개인 임시 경로로 전달됩니다.
바이트 수·SHA-256·원본 출처가 함께 반환됩니다. PDF·문서 분석과 이미지 열람은
호스트 도구가 별도로 수행합니다. 브리지는 문서 파싱·OCR·첨부 실행을 하지 않습니다.
최대 16개를 유지하며 사용이 끝난 파일은 `--release EXPORT_ID`로 해제합니다.
이후 내보내기나 `--cleanup`이 10분 지난 파일을 정리합니다. 백그라운드 삭제는 없고,
잠긴 파일이나 호스트·대화에 이미 전달된 사본은 남을 수 있습니다.

## 개인정보와 범위

메일함은 읽기 전용입니다. 발송·임시저장·삭제·이동·읽음 표시·강제 동기화·보안
정책 변경 기능은 없습니다. 답장 초안은 대화 안에만 작성합니다. 로컬 인덱스와
캐시가 오래됐거나 불완전할 수 있으므로 검색 결과 없음이 서버 메일 없음은 아닙니다.

MCP 서버·Cyp 백엔드·원격 메일 서비스·별도 API 키가 필요하지 않습니다. 다만
조회한 계정 정보·메일과 호스트가 연 파일은 요청 처리 과정에서 OpenAI로 전달될
수 있습니다. 로컬 실행이 GPT의 오프라인 처리를 뜻하지는 않습니다.

`THUNDERBIRD_HOME`은 프로필 등록 위치, `MAIL_BRIDGE_THUNDERBIRD_SETTINGS`는
개인 선택 설정 위치를 지정합니다. 기존 `THUNDERBIRD_BRIDGE_SETTINGS`도 지원합니다.
비밀번호·메일·프로필 절대경로는 선택 설정에 저장하지 않습니다. 기본 위치와
이전 버전 설정 호환성은 [영문 안내](README.md)에 있습니다.

[CLI 계약](docs/CLI.md) · [Thunderbird 호환성](docs/THUNDERBIRD_COMPATIBILITY.md) ·
[검증 범위](docs/RELEASE_VALIDATION.md) · [지원](docs/support.md) · [개인정보](docs/privacy.md)

Cyp의 독립 프로젝트이며 Mozilla나 OpenAI의 공식 제품이 아닙니다.

## 설치·계정 등록이 확인되지 않는 경우

먼저 `thunderbird_diagnostics`를 실행합니다. 설치가 탐지되지 않거나 등록된
프로필이 없으면 Thunderbird 설치·초기 설정을 안내하고, 지원 계정이 확인되지
않으면 Thunderbird에서 IMAP/POP3 계정을 추가하거나 설정 파일 접근 권한을
확인하도록 안내합니다. 인덱스가 없을 때는 전역 검색 활성화·동기화·인덱싱을
별도로 안내합니다. 진단 결과는 사용자 언어로 설명합니다.

진단은 메일 본문·비밀번호를 읽지 않으며 계정 주소나 프로필 경로를 반환하지
않습니다. 로컬 계정 설정 확인이 실제 로그인·인증 성공을 의미하지는 않습니다.
이동식 설치 등을 탐지하지 못해도 기존 프로필과 캐시가 있으면 사용할 수 있습니다.
상세 절차는 [설치·계정 안내](docs/SETUP.md)를 참고하세요.
