# Thunderbird Bridge

[English](README.md)

**Thunderbird 계정 하나의 로컬 메일을 Codex에서 검색·조회하는 Cyp Soft의 독립
데스크톱 플러그인**입니다. 무료이며 [MIT 라이선스](LICENSE)로 배포합니다.

> 도구는 PC에서 실행되지만, 조회한 계정 정보와 메일은 AI 서비스에 전달됩니다.
> 완전한 오프라인 AI 메일 도구가 아닙니다. 배포 소스에는 실제 계정·메일·설정이 없습니다.

## 기능

- Thunderbird 프로필과 IMAP/POP3 계정을 탐색합니다.
- 사용자가 명시적으로 선택한 계정 하나만 연결합니다.
- 키워드·발신자·수신자·폴더·기간으로 색인된 메일을 검색합니다.
- 본문과 대화를 조회하고 채팅에서 답장 초안을 작성합니다.
- 계정 선택 설정은 플러그인 밖의 사용자별 설정 폴더에 저장합니다.

별도 운영 서버·추적·분석·비밀번호 접근 기능은 없습니다. 메일을 발송하거나 삭제하지
않으며 계정 선택 시 자체 로컬 설정만 기록합니다. 프로필·계정 탐색 결과에도 이름,
메일 주소, 서버 정보가 포함될 수 있으므로 AI 호스트에 전달된다는 점을 확인하세요.

## 설치

Codex 플러그인을 지원하는 로컬 데스크톱 세션, PATH에 등록된 Node.js 18 이상,
Python 3.10 이상이 필요합니다. Thunderbird의 전체 검색·색인 기능을 활성화하고
메일 동기화를 마쳐야 합니다. 단독 웹·모바일 ChatGPT 연결은 제공하지 않습니다.

```sh
git clone https://github.com/Cyp9715/Thunderbird-Mail-Bridge.git
cd Thunderbird-Mail-Bridge
codex plugin marketplace add .
codex plugin add thunderbird-mail-bridge@cyp-soft-local
```

도구가 바로 보이지 않으면 앱을 새로고침하고 로컬 채팅에서 요청하세요.

> Thunderbird 프로필과 계정을 보여주고, 내가 선택하는 계정 하나만 연결해줘.

계정을 고른 뒤 “최근 메일 10개 요약해줘”, “프로젝트 관련 대화를 찾아줘”처럼
요청하면 됩니다. 설치 식별자 `thunderbird-mail-bridge`는 호환성을 위해 유지합니다.

## 범위

- 서버가 아닌 로컬 검색 색인을 읽으므로 최신 메일이 늦게 반영되거나 일부 메일이
  빠질 수 있습니다. 빈 결과가 서버에 메일이 없다는 뜻은 아닙니다.
- 본문은 원본 MIME 대신 색인 텍스트입니다. 첨부파일 이름만 조회합니다.
- 발송·삭제·이동·읽음 표시 변경·Thunderbird 초안 저장은 지원하지 않습니다.
- 날짜와 기간 검색은 UTC 기준입니다. 시작일은 포함하고 종료일은 포함하지 않습니다.
- Windows에서 검증했습니다. macOS/Linux의 실제 설치 환경 검증은 추가로 필요합니다.
- 회사·조직의 메일을 AI로 처리할 권한은 사용자가 확인해야 합니다.

설정 위치, 제거 방법, 합성 메일 테스트 방법은 [영문 README](README.md)를 참고하세요.

[지원](docs/support.md) · [개인정보 안내](docs/privacy.md) · [이용약관](docs/terms.md)

Thunderbird는 Mozilla Foundation의 상표입니다. Cyp Soft와 이 프로젝트는
Thunderbird·Mozilla·OpenAI의 공식 제품이나 제휴·후원·승인 제품이 아닙니다.
MIT 라이선스는 타사 상표나 로고 사용권을 부여하지 않습니다.
