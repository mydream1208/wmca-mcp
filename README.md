# WMCA MCP Server

NH투자증권(나무증권) WMCA DLL을 [MCP(Model Context Protocol)](https://modelcontextprotocol.io) 서버로 래핑한 프로젝트입니다.  
Claude Code CLI, Claude Desktop 등 MCP를 지원하는 AI 클라이언트에서 주식 시세 조회 및 주문을 자연어로 실행할 수 있습니다.

## 데모

```
사용자: 삼성전자 현재가 알려줘
Claude: 삼성전자(005930) 현재가 73,400원, 전일 대비 +800원 (13:24 기준)

사용자: 2번째 계좌 잔고 조회해줘
Claude: 계좌 20101398553 — 예수금 33,905,892원, KG이니시스 368주 보유 중
```

## 아키텍처

```
[AI 클라이언트]          [mcp_server.py]             [Windows]
  Claude Code   ──────►  FastMCP (stdio)  ──────►  WmcaHandler
  Claude Desktop          MCP 도구 정의              Win32 메시지 루프
  Cursor 등               asyncio Future             wmca.dll
                          WmcaBridge                 증권사 서버
```

**핵심 흐름:**
1. AI 클라이언트가 MCP 도구 호출 (예: `query_price("005930")`)
2. `mcp_server.py`가 asyncio Future를 등록하고 `WmcaHandler`로 DLL 함수 호출
3. WMCA DLL이 숨겨진 Win32 윈도우로 응답 메시지 전송
4. `wmca_proc.py`가 메시지를 파싱하고 `WmcaBridge`를 통해 Future를 resolve
5. `mcp_server.py`가 결과를 AI 클라이언트에 반환

## 요구사항

- **OS**: Windows 전용 (Win32 API 사용)
- **Python**: 3.9 이상
- **DLL**: 아래 파일들이 프로젝트 루트에 있어야 합니다 (NH투자증권 별도 제공)
  - `wmca.dll` (핵심 SDK)
  - `wmca.ini` (서버 접속 설정)
  - `libeay32.dll`, `librsa32.dll`, `nsldap32.dll`
  - `SKComd*.dll`, `SKComm*.dll`, `sha256w32.dll`, `CloudNPKI.dll`

> DLL 파일들은 NH투자증권 개발자 센터에서 신청 후 수령합니다.  
> 라이선스 문제로 이 저장소에는 포함되어 있지 않습니다.

## 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-id/wmca-mcp.git
cd wmca-mcp

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 본인의 계정 정보 입력
```

## 환경변수 설정 (`.env`)

```env
WMCA_USER_ID=나무증권_아이디
WMCA_USER_PW=비밀번호
WMCA_CERT_PW=공인인증서_비밀번호
```

> `.env` 파일은 `.gitignore`에 등록되어 있어 git에 올라가지 않습니다.  
> 환경변수가 설정되어 있으면 서버 시작 시 자동 로그인됩니다.

## 실행

```bash
python mcp_server.py
```

## MCP 클라이언트 등록

### Claude Code CLI (`.mcp.json`)

프로젝트 루트에 `.mcp.json` 파일 생성:

```json
{
  "mcpServers": {
    "wmca": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/절대경로/mcp_server.py"]
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

`%APPDATA%\Claude\claude_desktop_config.json` 에 추가:

```json
{
  "mcpServers": {
    "wmca": {
      "command": "python",
      "args": ["C:/절대경로/mcp_server.py"]
    }
  }
}
```

### MCP Inspector (테스트용)

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

## MCP 도구 목록

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `login` | NH투자증권 서버 로그인 | `user_id`, `user_pw`, `cert_pw` |
| `get_accounts` | 로그인된 계좌 목록 조회 | — |
| `query_price` | 주식 현재가 조회 | `code` (종목코드), `market` |
| `query_balance` | 계좌 잔고 조회 | `acc_index` (1부터), `account_no`, `account_pwd` |
| `sell_order` | 매도 주문 | `acc_index`, `account_pwd`, `order_pwd`, `code`, `price`, `qty` |
| `subscribe_realtime` | 실시간 시세 구독 시작 | `code` |
| `get_realtime_data` | 실시간 체결 데이터 조회 | `code`, `count` |
| `get_messages` | 서버 수신 메시지 조회 | `count` |
| `disconnect` | 서버 연결 해제 | — |

> `acc_index`는 `get_accounts` 반환 목록의 순서 (1번부터 시작)

## 파일 구조

```
wmca-mcp/
├── mcp_server.py      # FastMCP 서버 — MCP 도구 정의 및 진입점
├── wmca_bridge.py     # asyncio ↔ Win32 스레드 브리지 (Future 관리)
├── wmca_handler.py    # Win32 메시지 루프 및 DLL 호출
├── wmca_client.py     # ctypes DLL 로더 및 함수 시그니처 바인딩
├── wmca_proc.py       # Win32 메시지 디스패처 및 응답 파서
├── wmca_def.py        # 공통 상수 및 로그인/계좌 ctypes 구조체
├── trio_inv.py        # 시세/투자 데이터 ctypes 구조체 (현재가 등)
├── trio_ord.py        # 주문/잔고 ctypes 구조체 (잔고조회, 매도 등)
├── app.py             # PyQt5 GUI 클라이언트 (MCP 없이 직접 실행)
├── .env.example       # 환경변수 템플릿 (복사 후 .env로 사용)
├── .gitignore
├── requirements.txt
└── wmca.ini           # 서버 접속 설정 (git 제외, DLL과 함께 제공)
```

## ctypes 구조체 규칙

새 TR을 추가할 때 참고할 규칙입니다.

- `_pack_ = 1` — 1바이트 정렬 필수 (DLL 전문 규격)
- `_fieldname` 접미사 — 전문 구분자용 1바이트 패딩 필드
- 입력 구조체 초기화 — `ctypes.memset(..., 0x20)` (공백 0x20, 제로 아님)
- 문자열 인코딩 — `cp949` (한국어 EUC-KR)

## 보안 주의사항

- `.env` 파일을 절대 git에 커밋하지 마세요.
- DLL 파일도 라이선스 문제로 커밋하지 마세요.
- 주문(매도/매수) 도구는 실제 거래로 이어지므로 신중하게 사용하세요.

## 라이선스

MIT — 단, WMCA DLL 및 관련 바이너리는 NH투자증권 라이선스를 따릅니다.
