"""
mcp_server.py
─────────────────────────────────────────────────────────────────────────────
NH투자증권(나무증권) WMCA DLL을 MCP 도구(Tool)로 노출하는 FastMCP 서버.

WMCA DLL은 Win32 메시지 기반 비동기 API입니다.
이 서버는 asyncio Future를 사용해 Win32 콜백을 await 가능한 형태로 변환합니다.

  [MCP 클라이언트]  →  [mcp_server.py]  →  [WmcaHandler]  →  [wmca.dll]
       (Claude)          (FastMCP)          (Win32 스레드)     (증권사 서버)

─────────────────────────────────────────────────────────────────────────────
실행:
    python mcp_server.py

자동 로그인 (환경변수 설정 시 서버 시작과 함께 로그인):
    .env 파일에 아래 값을 설정하세요 (.env.example 참고)
        WMCA_USER_ID=your_id
        WMCA_USER_PW=your_password
        WMCA_CERT_PW=your_cert_password

MCP Inspector로 테스트:
    npx @modelcontextprotocol/inspector python mcp_server.py

Claude Code CLI 등록 (.mcp.json):
    {
      "mcpServers": {
        "wmca": {
          "type": "stdio",
          "command": "python",
          "args": ["C:/path/to/mcp_server.py"]
        }
      }
    }

─────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import logging
import sys
import builtins
import os
from contextlib import asynccontextmanager

# .env 파일에서 환경변수 로드 (파일이 없으면 무시)
from dotenv import load_dotenv
load_dotenv()

# MCP stdio 모드에서 stdout은 JSON-RPC 전용 파이프.
# print()가 stdout으로 나가면 프로토콜이 깨지므로 stderr로 리다이렉트.
# 또한 cp949 터미널에서 이모지 등 인코딩 오류도 무시.
_orig_print = builtins.print
def _safe_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    try:
        _orig_print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        pass
builtins.print = _safe_print

from mcp.server.fastmcp import FastMCP
from wmca_def import TRID_IVWUTKMST04, TRID_C8201, TRID_C8101

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 전역 상태 (lazy 초기화)
# ------------------------------------------------------------------
_bridge = None
_handler = None


async def _init_if_needed():
    """처음 호출 시 WmcaBridge + WmcaHandler를 초기화하고 Win32 윈도우 생성 대기."""
    global _bridge, _handler
    if _bridge is None:
        from wmca_bridge import WmcaBridge
        from wmca_handler import WmcaHandler

        _bridge = WmcaBridge()
        _bridge.loop = asyncio.get_running_loop()
        _handler = WmcaHandler(_bridge)

        ready = await _handler.wait_ready(timeout=5.0)
        if not ready:
            _bridge = None
            _handler = None
            raise RuntimeError("Win32 핸들러 초기화 타임아웃 (5초)")

        logger.info("WmcaHandler 초기화 완료, HWND 생성됨")

    return _bridge, _handler


def _require_connection():
    """연결 상태 확인. 미연결 시 예외 발생."""
    if _bridge is None or _handler is None:
        raise RuntimeError("초기화되지 않음. login을 먼저 호출하세요.")
    if not _bridge.is_connected:
        raise RuntimeError("서버에 연결되지 않음. login을 먼저 호출하세요.")
    return _bridge, _handler


# ------------------------------------------------------------------
# FastMCP 서버 정의 + 자동 로그인 (환경변수 설정 시)
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server):
    """서버 시작/종료 훅.

    환경변수(WMCA_USER_ID, WMCA_USER_PW, WMCA_CERT_PW)가 모두 설정된 경우
    서버 시작 시 자동으로 로그인을 시도합니다.
    """
    user_id = os.getenv("WMCA_USER_ID")
    user_pw  = os.getenv("WMCA_USER_PW")
    cert_pw  = os.getenv("WMCA_CERT_PW")

    if user_id and user_pw and cert_pw:
        logger.info("환경변수 감지 — 자동 로그인 시도 중...")
        try:
            result = await login(user_id, user_pw, cert_pw)
            logger.info(f"자동 로그인 결과: {result.get('status')}")
        except Exception as e:
            logger.warning(f"자동 로그인 실패 (수동으로 login 도구를 호출하세요): {e}")
    else:
        logger.info("환경변수 미설정 — login 도구로 수동 로그인이 필요합니다.")

    yield  # 서버 실행 중

    # 서버 종료 시 연결 해제
    if _handler is not None:
        logger.info("서버 종료 — WMCA 연결 해제 중...")
        _handler.disconnect_server()


mcp = FastMCP("WMCA 주식 거래 서버", lifespan=lifespan)


@mcp.tool()
async def login(user_id: str, user_pw: str, cert_pw: str) -> dict:
    """NH투자증권(나무증권) 서버에 로그인합니다.

    Args:
        user_id: 사용자 ID
        user_pw: 사용자 비밀번호
        cert_pw: 공인인증서 비밀번호

    Returns:
        {"status": "connected", "accounts": [...]} 형태의 결과.
        accounts 각 항목: {"계좌번호": ..., "계좌명": ..., "상품코드": ...}
    """
    bridge, handler = await _init_if_needed()

    if bridge.is_connected:
        return {"status": "already_connected", "accounts": bridge.accounts}

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    bridge.register_request("login", future)

    handler.connect_server(user_id, user_pw, cert_pw)

    try:
        result = await asyncio.wait_for(future, timeout=30.0)
        return result
    except asyncio.TimeoutError:
        raise RuntimeError("로그인 타임아웃 (30초). ID/PW/인증서 비밀번호를 확인하세요.")


@mcp.tool()
async def get_accounts() -> list:
    """로그인 후 계좌 목록을 반환합니다.

    Returns:
        [{"계좌번호": ..., "계좌명": ..., "상품코드": ...}, ...]
    """
    bridge, _ = _require_connection()
    return bridge.accounts


@mcp.tool()
async def query_price(code: str, market: str = "UNT") -> dict:
    """주식 현재가를 조회합니다.

    Args:
        code: 종목코드 (예: "005930" 삼성전자, "035720" 카카오)
        market: 시장 코드. "UNT"=통합시세(기본), "KRX"=거래소, "NXT"=넥스트

    Returns:
        {"종목코드": ..., "현재가": ..., "시간": ..., "부호": ...,
         "대비": ..., "시가": ..., "고가": ..., "저가": ..., "거래량": ...}
    """
    bridge, handler = _require_connection()

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    bridge.register_request(TRID_IVWUTKMST04, future)

    handler.query_price(code, market)

    try:
        data_list = await asyncio.wait_for(future, timeout=10.0)
        if data_list:
            return data_list[0]
        return {"error": "데이터 없음"}
    except asyncio.TimeoutError:
        raise RuntimeError(f"현재가 조회 타임아웃: {code}")


@mcp.tool()
async def query_balance(acc_index: int, account_no: str, account_pwd: str) -> list:
    """주식 잔고를 조회합니다.

    Args:
        acc_index: 계좌 인덱스 (1부터 시작. get_accounts 결과의 순서)
        account_no: 계좌번호 (예: "12345678901")
        account_pwd: 계좌 비밀번호

    Returns:
        리스트. 첫 항목은 계좌 요약(구분="계좌"), 이후 항목은 보유 종목(구분="잔고").
        계좌 요약: {"구분": "계좌", "예수금": ..., "출금가능금액": ..., ...}
        보유 종목: {"구분": "잔고", "종목코드": ..., "종목명": ..., "잔고수량": ...}
    """
    bridge, handler = _require_connection()

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    bridge.register_request(TRID_C8201, future)

    handler.query_balance(acc_index, account_no, account_pwd)

    try:
        data_list = await asyncio.wait_for(future, timeout=10.0)
        return data_list
    except asyncio.TimeoutError:
        raise RuntimeError("잔고 조회 타임아웃")


@mcp.tool()
async def sell_order(
    acc_index: int,
    account_pwd: str,
    order_pwd: str,
    code: str,
    price: int,
    qty: int,
) -> dict:
    """매도 주문을 전송합니다.

    Args:
        acc_index: 계좌 인덱스 (1부터 시작. get_accounts 결과의 순서)
        account_pwd: 계좌 비밀번호
        order_pwd: 주문(거래) 비밀번호
        code: 종목코드 (예: "005930")
        price: 주문 단가 (원). 0이면 시장가
        qty: 주문 수량 (주)

    Returns:
        {"status": "주문 전송됨", "data": [...]} 또는 오류 시 예외
    """
    bridge, handler = _require_connection()

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    bridge.register_request(TRID_C8101, future)

    handler.sell_order(acc_index, account_pwd, order_pwd, code, price, qty)

    try:
        data_list = await asyncio.wait_for(future, timeout=10.0)
        return {"status": "주문 전송됨", "data": data_list}
    except asyncio.TimeoutError:
        raise RuntimeError("매도 주문 타임아웃")


@mcp.tool()
async def subscribe_realtime(code: str, market: str = "UNT") -> dict:
    """실시간 시세(체결) 구독을 시작합니다.

    구독 후 get_realtime_data(code)로 최신 체결 데이터를 조회할 수 있습니다.

    Args:
        code: 종목코드 (예: "005930")
        market: 시장 코드 (기본값: "UNT")

    Returns:
        {"status": "구독 요청됨", "code": ..., "res": ...}
    """
    bridge, handler = _require_connection()
    res = handler.attach_price(code, market)
    return {"status": "구독 요청됨", "code": code, "res": res}


@mcp.tool()
async def get_realtime_data(code: str, count: int = 10) -> list:
    """구독 중인 종목의 실시간 체결 데이터를 반환합니다.

    subscribe_realtime(code)를 먼저 호출해야 데이터가 수신됩니다.
    주문 체결/통보는 code="d2_orders" 또는 code="d3_orders"로 조회합니다.

    Args:
        code: 종목코드, 또는 "d2_orders"(체결통보), "d3_orders"(주문통보)
        count: 반환할 최대 항목 수 (기본값: 10, 최신 순)

    Returns:
        [{"종목코드": ..., "가격": ..., "시간": ..., "대비": ...}, ...]
    """
    bridge, _ = _require_connection()
    buf = bridge.realtime_buffer.get(code)
    if not buf:
        return []
    return list(buf)[:count]


@mcp.tool()
async def get_messages(count: int = 20) -> list:
    """서버에서 수신한 메시지(알림, 오류 포함) 목록을 반환합니다.

    Args:
        count: 반환할 최대 항목 수 (기본값: 20, 최신 순)

    Returns:
        메시지 문자열 리스트
    """
    if _bridge is None:
        return []
    return list(_bridge.messages)[:count]


@mcp.tool()
async def disconnect() -> dict:
    """서버 연결을 해제합니다.

    Returns:
        {"status": "연결 해제 요청됨"}
    """
    if _handler is not None:
        _handler.disconnect_server()
    return {"status": "연결 해제 요청됨"}


# ------------------------------------------------------------------
# 진입점
# ------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
