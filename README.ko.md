# Codex용 Mail Bridge

[English](README.md)

**Thunderbird·클래식 Outlook 메일을 Codex에서 검색·조회하는 Cyp Soft 플러그인**입니다.
Office 2019를 지원하며 Microsoft 365 구독은 필요하지 않습니다. 무료이며 MIT 라이선스입니다.

**사용 전에 Thunderbird 또는 클래식 Outlook에 로그인하고 필요한 메일을 동기화해야 합니다.**
클래식 Outlook은 로그인한 프로필로 실행해 두세요. 플러그인이 대신 로그인하지 않습니다.
Thunderbird는 이미 저장된 색인·캐시가 있으면 창이 닫힌 상태에서도 조회할 수 있습니다.

메일함에 대한 접근은 **읽기 전용**입니다. 메일 검색·본문 조회·요약·대화 정리와 채팅에서의
답장 문안 작성을 지원합니다. 메일 작성 창 열기, 발송, Thunderbird/Outlook 초안 저장,
삭제, 이동, 읽음 표시 변경은 지원하지 않습니다. 계정 선택 설정과 요청한 첨부의 임시 로컬 복사본만 저장합니다.

배포 소스에는 실제 메일·계정 설정·비밀번호·PST/OST·개인 PC 경로가 없습니다.
도구는 PC에서 실행되지만 조회한 계정 정보와 메일은 AI 서비스에 전달됩니다.

## 지원 범위

| 클라이언트 | 접근 방식 | 검증 범위 |
| --- | --- | --- |
| Thunderbird | 등록된 프로필·로컬 색인·선택 메일의 MIME 캐시 | IMAP/POP3, Windows 실제 동작 검증 |
| Windows 클래식 Outlook | 실행 중인 Outlook의 COM API | Office Standard 2019 64비트 실제 동작 검증, Microsoft 365 구독 불필요 |
| 새 Outlook·웹 Outlook·Mac Outlook | 제공하지 않음 | 클래식 Windows COM 방식의 대상이 아님 |

다른 PC·Office 버전 전체에서 검증한 것은 아닙니다. macOS/Linux의 Thunderbird 프로필
탐색은 합성 테스트를 통과했으며 실제 해당 OS 설치 환경 검증은 추가로 필요합니다.
[호환성 검토](docs/OUTLOOK_COMPATIBILITY.md)와 [이식성](docs/PORTABILITY.md)에 범위를 구분했습니다.

## 설치와 사용

로컬 Codex 데스크톱 플러그인 지원, Node.js 18 이상, Python 3.10 이상이 필요합니다.
Outlook은 Windows PowerShell 5.1과 실행 중인 클래식 Outlook 프로필도 필요합니다.
Thunderbird는 전체 검색·색인 기능이 활성화돼 있어야 합니다.

```sh
git clone https://github.com/Cyp9715/Codex-Mail-Bridge.git
cd Codex-Mail-Bridge
codex plugin marketplace add .
codex plugin add codex-mail-bridge@cyp-soft-local
```

도구가 바로 나타나지 않으면 앱을 새로고침하세요. 예를 들어 다음처럼 요청합니다.

- “클래식 Outlook 계정을 보여주고 내가 고르는 계정 하나만 연결해 줘.”
- “Thunderbird에서 이번 달 프로젝트 관련 메일을 찾아 요약해 줘.”
- “Thunderbird에서 2026년 10월 이후의 첨부파일을 찾아 줘.”
- “Outlook에서 이번 주에 받은 메일의 필요한 첨부파일을 확인해 줘.”
- “Outlook의 최근 대화에서 내가 해야 할 일을 정리해 줘.”

각 클라이언트에서 명시적으로 선택한 계정 하나에만 접근합니다. 어느 클라이언트를
말하는지 불분명하면 먼저 확인하며, 두 메일함을 자동으로 합쳐 검색하지 않습니다.
기존 로컬 설치는 `thunderbird-bridge` 또는 0.1.x의 `thunderbird-mail-bridge` 식별자로
제거한 뒤 새 식별자로 설치하세요. 계정 선택은 패키지 밖에 저장되어 유지됩니다.

## 경로와 계정 보호

특정 PC의 메일 경로를 고정하지 않습니다. Thunderbird는 `profiles.ini`에 등록된
상대·절대 경로를 탐색하며 다른 등록 위치는 `THUNDERBIRD_HOME`으로 지정할 수 있습니다.
Outlook은 현재 실행 중인 프로필에서 계정과 저장소를 찾습니다. PST/OST 경로를 추정하거나
직접 파싱하지 않습니다. 여러 계정이 같은 저장소를 공유하면 계정 분리가 불분명해 연결을 거부합니다.

사용자별 `CypSoft/MailBridge` 설정 폴더에 `thunderbird.json`, `outlook.json`을 별도로
저장합니다. 설정에는 불투명한 ID와 계정 확인용 지문만 있고 주소·비밀번호·메일은 없습니다.
이전 Thunderbird 선택 설정도 읽을 수 있으며, 조회만으로 설정을 옮기거나 수정하지 않습니다.
새 설정이 잘못되었을 때 이전 계정으로 우회하지 않습니다. 자세한 위치와 환경 변수는 영문 README를 참고하세요.

## 결과의 한계

- Thunderbird는 로컬 색인만 읽으므로 메일이나 본문이 빠지거나 최신 메일이 늦게 반영될 수 있습니다.
- Outlook은 선택 계정의 고유 배달 저장소에서 받은·보낸 일반 메일을 조회합니다. 별도 보관 PST,
  가상 검색 폴더, 휴지통, 임시 보관함, 보낼 편지함은 제외합니다.
- Outlook 검색은 최신 후보 기본 1,000개, 최대 5,000개와 시간 제한 안에서 동작합니다.
  `scan_incomplete`가 참이면 일부 범위만 검색한 것입니다. 본문 검색은 메일당 최대 6,000자이며
  본문·수신자·첨부 이름이 잘렸는지도 표시합니다. 빈 결과가 전체 메일함에 없다는 뜻은 아닙니다.
- 날짜는 `time_zone`의 자정 기준으로 시작일 포함·종료일 제외입니다. 기본은 UTC이며
  한국 날짜에는 `time_zone:"+09:00"`을 지정합니다. Outlook은 기간을 먼저 적용한 뒤 후보 수를 제한합니다.
- Outlook 자체 공급자가 네트워크에서 데이터를 가져올 수 있어 완전한 오프라인 동작을 보장하지 않습니다.
  보안 경고나 조직 정책을 우회하거나 보안 설정을 바꾸지 않습니다.

별도 운영 서버·분석·추적·결제 기능은 없습니다. 회사 메일을 AI 서비스로 처리할 권한과
AI 호스트의 데이터 정책은 사용자가 확인해야 합니다.

0.4.0은 **제목·기간·발신자·첨부파일명 검색 → 메일 하나의 첨부 목록 → 필요한 원본만 전달**을 지원합니다.
각 클라이언트에 `*_search_attachments`, `*_list_attachments`, `*_get_attachment`가 추가되어 총 19개 도구입니다.
검색은 본문과 파일 내용을 읽지 않고 메타데이터만 기본 10개·최대 20개 반환합니다. 첨부가 많아도 모두 열거나
일괄 전달하지 않습니다. 선택한 파일은 최대 10 MiB 원본 그대로 임시 경로·해시·리소스 링크로 제공하며,
0.5.0부터 이미지 응답은 분석이 필요할 때 `include_image:true`로 요청합니다. 기본값 false에서도 원본 파일은 전달됩니다.
PDF·Word·Excel 등의 파서나 OCR은 넣지 않았습니다. Codex의 파일 도구로 원본을 사용할 수 있으며, 전달만으로
모든 문서 형식의 분석이나 클라우드 업로드가 보장되지는 않습니다.

Thunderbird는 설정에 등록된 로컬 MIME 캐시가 있어야 하며 안전하게 찾을 수 없는 경로나 검색 한계 밖의 메일은
가져오지 않습니다. Outlook은 일반 파일 첨부를 지원하며 링크·OLE·메일 자체 첨부·보호 메일은 제외합니다.
임시 복사본은 최대 16개이며 10분 후 다음 전달/리소스 요청 때 정리하고 정상 종료 시에도 정리를 시도합니다.
비정상 종료·파일 잠금 시 복사본이 남을 수 있습니다. 새 기능은 가상 메일과 생성 파일로 검증했으며 실제 Outlook
공급자·설치된 Codex 연결·다른 PC에서의 첨부 전달 검증은 남아 있습니다. 자세한 범위는
[첨부 원본 전달 문서](docs/ATTACHMENT_SUPPORT.md)를 참고하세요.

## 기간 조회와 필요한 만큼 읽기

아래 옵션은 Thunderbird·Outlook의 일반 메일 검색과 첨부 검색 모두에 적용됩니다.
상대 기간은 현재 시각과 지정 시간대를 기준으로 계산하며 한 주는 월요일에 시작합니다.

| 요청 | 도구에 전달되는 기간 옵션 예시 |
| --- | --- |
| “2026년 10월 이후” | `after:"2026-10-01", time_zone:"+09:00"` (종료일 없음) |
| “이번 주” | `period:"this_week", time_zone:"+09:00"` |
| “지난주” | `period:"last_week", time_zone:"+09:00"` |
| “이번 달” / “지난달” | `period:"this_month"` / `period:"last_month"`, 사용자 `time_zone` 지정 |
| “10월 한 달만” | `after:"2026-10-01", before:"2026-11-01", time_zone:"+09:00"` |

연도가 생략되면 대화 맥락에서 정하며 불분명할 때 확인합니다. 상대 기간 `period`와
명시적 날짜 `after/before`를 함께 보내면 오류로 처리합니다. 응답의 `date_range`에
실제 검색한 UTC 경계를 표시합니다. `+09:00`은 추가 설치 없이 사용할 수 있습니다.
IANA 시간대 이름은 로컬 시간대 데이터가 필요하며 Windows에서는 선택적으로 `tzdata`가 필요할 수 있습니다.

0.5.0의 일반 검색은 기본적으로 길이가 제한된 메타데이터를 반환하고, 필요한 경우에만
`include_snippet:true`로 280자 본문 미리보기를 받습니다. 본문은 `next_body_offset`으로
다음 구간을 읽을 수 있습니다. 대화 조회는 기본 총 24,000자이며 필요한 경우
`max_total_characters`로 최대 120,000자까지 늘리거나 개별 메일을 이어 읽을 수 있습니다.
이는 문자 수 기준이며 정확한 토큰 수를 보장하지 않습니다.

넓은 검색이 필요하면 결과 페이지를 읽은 뒤 Outlook의 `next_scan_offset`으로 후보 범위를
이어 읽습니다. 후보 오프셋 한도 100,000이나 시간 제한에 도달하면 기간·폴더를 나눠 검색합니다.
메일이 추가·이동되면 범위가 달라질 수 있어 ID로 중복을 제거합니다. 여러 파일을 요청한 경우에도
필요한 원본을 나눠 전달하고 분석할 수 있으며, 기본 페이지 크기가 작업 전체의 한도는 아닙니다.
[설계 검토와 후속 제안](docs/DESIGN_REVIEW.md)에 판단 근거와 남은 검증 범위를 기록했습니다.

개발 시에는 [공개 전 검사 절차](docs/DEVELOPMENT_SECURITY.md)를 따릅니다. 실제 메일과
계정 식별자를 소스·커밋 메시지·이슈에 넣지 않으며, 보호할 문자열은 Git에서 제외되는
개인별 파일에만 둡니다. 커밋·푸시·ZIP 생성 전 검사로 실수로 포함된 정보를 차단합니다.

## 테스트와 공개 등록

```sh
python -m unittest discover -s plugins/codex-mail-bridge/tests -p "test_*.py"
python scripts/package.py --output ./outputs
```

합성 테스트와 실제 Office 2019 검증을 구분해 기록했습니다. 공개 데모에는 가상 메일만 사용합니다.
OpenAI 공개 디렉터리 등록은 별도 절차이며, 로컬 MCP 제출 조직 승인·개발자 인증·검증된 데모 영상이
필요합니다. 현재 저장소 공개나 ZIP 생성이 OpenAI 심사 통과를 뜻하지 않습니다.

[지원](docs/support.md) · [개인정보](docs/privacy.md) · [이용약관](docs/terms.md) · [제출 준비](docs/SUBMISSION.md)

Mail Bridge는 Cyp Soft의 독립 프로젝트이며 Thunderbird·Mozilla·Microsoft·OpenAI의
공식·제휴·후원·승인 제품이 아닙니다. 타사 제품명은 호환 대상을 설명하며 타사 로고를 사용하지 않습니다.
