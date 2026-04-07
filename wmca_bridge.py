"""
wmca_bridge.py
asyncio 이벤트 루프 ↔ Win32 메시지 스레드 사이의 브리지 레이어.

MCP 도구 함수(async)에서 future를 등록하고,
Win32 스레드(process_msg)에서 결과 도착 시 future를 해결합니다.
"""

import asyncio
import threading
from collections import deque
import logging

logger = logging.getLogger(__name__)


class WmcaBridge:
    """asyncio ↔ Win32 스레드 브리지"""

    def __init__(self):
        # MCP 서버 시작 후 asyncio 이벤트 루프를 직접 할당해야 함
        self.loop: asyncio.AbstractEventLoop = None

        self._lock = threading.Lock()
        # key: TRID(int) 또는 "login" → {"future": Future, "data": list}
        self._pending: dict = {}

        # 실시간 데이터 버퍼: code → deque(maxlen=100)
        self.realtime_buffer: dict = {}

        # 로그인 후 계좌 목록
        self.accounts: list = []

        # 연결 상태
        self.is_connected: bool = False

        # 일반 메시지 버퍼 (최신 200개 유지)
        self.messages: deque = deque(maxlen=200)

    # ------------------------------------------------------------------
    # asyncio 스레드에서 호출 — 요청 등록
    # ------------------------------------------------------------------

    def register_request(self, key, future: asyncio.Future):
        """MCP 도구에서 DLL 요청을 보내기 전에 future를 등록."""
        with self._lock:
            self._pending[key] = {"future": future, "data": []}

    # ------------------------------------------------------------------
    # Win32 스레드에서 호출 — 결과 저장
    # ------------------------------------------------------------------

    def append_data(self, key, data: dict):
        """CA_RECEIVEDATA 수신 시 데이터 누적 (CA_RECEIVECOMPLETE 전에 여러 번 호출될 수 있음)."""
        with self._lock:
            if key in self._pending:
                self._pending[key]["data"].append(data)

    def complete_request(self, key):
        """CA_RECEIVECOMPLETE 수신 시 future를 resolve."""
        with self._lock:
            pending = self._pending.pop(key, None)
        if pending is None:
            return
        future = pending["future"]
        data = pending["data"]
        if self.loop:
            self.loop.call_soon_threadsafe(self._safe_set_result, future, data)

    def fail_request(self, key, error_msg: str):
        """CA_RECEIVEERROR 수신 시 future를 reject."""
        with self._lock:
            pending = self._pending.pop(key, None)
        if pending is None:
            return
        future = pending["future"]
        if self.loop:
            self.loop.call_soon_threadsafe(
                self._safe_set_exception, future, Exception(error_msg)
            )

    # ------------------------------------------------------------------
    # 이벤트 핸들러 (Win32 스레드에서 호출)
    # ------------------------------------------------------------------

    def on_connected(self, accounts: list):
        """CA_CONNECTED 수신 시 호출 — login future를 resolve."""
        self.accounts = accounts
        self.is_connected = True
        with self._lock:
            pending = self._pending.pop("login", None)
        if pending and self.loop:
            future = pending["future"]
            result = {"status": "connected", "accounts": accounts}
            self.loop.call_soon_threadsafe(self._safe_set_result, future, result)

    def on_disconnected(self):
        """CA_DISCONNECTED 수신 시 호출."""
        self.is_connected = False
        self.add_message("서버 연결 끊김 (CA_DISCONNECTED)")

    def add_realtime(self, code: str, data: dict):
        """실시간 시세 데이터를 버퍼에 추가."""
        if code not in self.realtime_buffer:
            self.realtime_buffer[code] = deque(maxlen=100)
        self.realtime_buffer[code].appendleft(data)

    def add_message(self, msg: str):
        """일반 메시지를 버퍼에 추가. login이 pending 중이면 결과로 전달."""
        self.messages.appendleft(msg)
        logger.info(msg)
        # login 대기 중이면 서버 메시지를 login 결과로 반환 (오류 포함)
        with self._lock:
            pending = self._pending.get("login")
        if pending and self.loop:
            future = pending["future"]
            self.loop.call_soon_threadsafe(
                self._safe_set_result, future,
                {"status": "message", "message": msg, "accounts": self.accounts}
            )

    def add_error_message(self, trid, msg_cd: str, user_msg: str):
        """CA_RECEIVEERROR 처리 — 해당 TRID의 future를 reject하고 메시지 기록."""
        error_msg = f"[{msg_cd}] {user_msg}"
        self.add_message(f"ERROR TRID={trid}: {error_msg}")
        self.fail_request(trid, error_msg)

    # ------------------------------------------------------------------
    # 내부 유틸리티
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_set_result(future: asyncio.Future, result):
        if not future.done():
            future.set_result(result)

    @staticmethod
    def _safe_set_exception(future: asyncio.Future, exc: Exception):
        if not future.done():
            future.set_exception(exc)
