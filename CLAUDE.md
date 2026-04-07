# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 안내 문서입니다.

## 프로젝트 개요

이 프로젝트는 **한국 주식 거래 데스크톱 애플리케이션**으로, NH투자증권(나무증권)의 자체 브로커리지 SDK인 WMCA(Windows Message-based Communication API) DLL을 래핑합니다. PyQt5 GUI 클라이언트로 구현되어 있으며, 증권사 서버에 접속해 주식 시세를 조회하고 Win32 메시지 시스템을 통해 주문을 전송합니다.

## 아키텍처

애플리케이션은 계층형 구조로 설계되어 있습니다:

```
app.py (PyQt5 UI / MainWindow)
    └── wmca_handler.py (WmcaHandler : QObject)
            ├── wmca_client.py (WmcaClient — ctypes DLL 래퍼)
            ├── wmca_proc.py (process_msg — Win32 메시지 디스패처)
            ├── wmca_def.py (공통 상수 및 기본 구조체)
            ├── trio_inv.py (시세/투자 데이터 구조체)
            └── trio_ord.py (주문/잔고 구조체)
```

**핵심 설계 패턴:** `WmcaHandler`는 백그라운드 스레드에서 보이지 않는 Win32 메시지 전용 윈도우를 생성합니다. WMCA DLL은 이 숨겨진 HWND로 Windows 메시지(`CA_WMCAEVENT = WM_USER+8400`)를 전송하여 응답을 전달합니다. `wmca_proc.py`가 이 메시지들을 처리하고 PyQt5 시그널을 통해 UI 스레드로 데이터를 전달합니다.

### DLL 연동 흐름
1. `WmcaClient._bind()`에서 모든 DLL 함수의 ctypes argtypes/restypes를 등록
2. `WmcaHandler._msg_loop_thread()`에서 숨겨진 Win32 윈도우를 생성하고 `PumpMessages()` 실행
3. `wmcaConnect`, `wmcaQuery`, `wmcaAttach` 등의 DLL 함수를 숨겨진 HWND와 함께 호출
4. DLL 응답 → Win32 메시지 → `_wnd_proc` → `process_msg` → PyQt5 시그널 → UI

### 메시지 상수 (`wmca_def.py`)
- `CA_WMCAEVENT` (WM_USER+8400): 단일 외부 메시지 타입; `wparam`으로 세부 유형 구분
- 세부 유형: `CA_CONNECTED` (1134), `CA_DISCONNECTED` (1144), `CA_RECEIVEDATA` (1234), `CA_RECEIVESISE` (1244), `CA_RECEIVEMESSAGE` (1254), `CA_RECEIVECOMPLETE` (1264), `CA_RECEIVEERROR` (1274)
- TR ID: `TRID_IVWUTKMST04` (4000, 현재가 조회), `TRID_C8201` (5000, 잔고조회), `TRID_C8101` (6000, 매도주문)

### ctypes 구조체 규칙
- 모든 구조체는 `_pack_ = 1` (1바이트 정렬) 사용
- `_fieldname` 접미사 필드는 전문 구분자용 1바이트 패딩
- 입력 구조체는 `ctypes.memset(..., 0x20)`으로 초기화 (제로 초기화가 아닌 공백 초기화)
- 문자열 인코딩/디코딩은 `cp949` (한국어 EUC-KR) 사용

## 실행 방법

```bash
python app.py
```

**환경 요구사항:**
- Windows 전용 (`pywin32`를 통한 `win32gui`, `win32con`, `win32api` 사용)
- PyQt5
- 동일 디렉터리에 `wmca.dll` 및 의존 DLL 필요 (`libeay32.dll`, `librsa32.dll`, `nsldap32.dll`, `SKComd*.dll`, `SKComm*.dll`, `sha256w32.dll`, `CloudNPKI.dll`)
- 동일 디렉터리에 `wmca.ini` 필요 (서버 설정 파일)

## 주요 파일

| 파일 | 역할 |
|------|------|
| `app.py` | PyQt5 `MainWindow` — UI 레이아웃 및 시그널 핸들러 전체 |
| `wmca_handler.py` | `WmcaHandler` — 비즈니스 로직, DLL 호출, Win32 메시지 루프 |
| `wmca_client.py` | `WmcaClient` — ctypes DLL 로더 및 함수 바인딩 |
| `wmca_proc.py` | `process_msg` — Win32 메시지 디스패처 및 데이터 파서 |
| `wmca_def.py` | 상수, `LOGINBLOCK`/`LOGININFO`/`ACCOUNTINFO`, `OUTDATABLOCK`, `RECEIVED`, `MSGHEADER` |
| `trio_inv.py` | 시세/시장 데이터 구조체 (`IVWUTKMST04`, `mc` 실시간 체결, `mb` 호가) |
| `trio_ord.py` | 주문/잔고 구조체 (`c8101` 매도, `c8201` 잔고, `d2`/`d3` 주문 통보) |
| `wmca.ini` | 서버 연결 설정 (로그 레벨, 서버/포트 선택적 지정) |

## 새 TR 조회 추가 방법

1. `trio_inv.py` 또는 `trio_ord.py`에 입출력 ctypes 구조체 정의 (`_pack_ = 1`, 공백 초기화, `_fieldname` 구분자 적용)
2. `wmca_def.py`에 `TRID_*` 상수 추가
3. `wmca_handler.py`에 입력 블록을 구성하고 `wmcaQuery`를 호출하는 메서드 추가
4. `wmca_proc.py`의 `CA_RECEIVEDATA` 또는 `CA_RECEIVESISE` 분기에서 응답 처리
5. `WmcaHandler`에서 PyQt5 시그널을 emit하고 `app.py`에서 연결
