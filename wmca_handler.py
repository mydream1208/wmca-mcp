"""
wmca_handler.py
─────────────────────────────────────────────────────────────────────────────
Win32 메시지 루프를 전담하는 핸들러.

WMCA DLL은 호출자가 Win32 윈도우를 소유해야 합니다.
이 클래스는 별도 스레드에서 숨겨진 Win32 윈도우를 생성하고
`PumpMessages()`로 메시지 루프를 실행합니다.

DLL 호출 흐름:
    asyncio 스레드  →  PostMessage(_WM_*)  →  Win32 스레드  →  DLL 함수 실행
                                              ↓
    asyncio Future  ←  call_soon_threadsafe  ←  WmcaBridge  ←  _wnd_proc 응답
─────────────────────────────────────────────────────────────────────────────
"""

from trio_inv import *
from trio_ord import *
from wmca_def import *
import threading
import ctypes
import asyncio
import win32gui
import win32con
import win32api
import logging
from wmca_client import WmcaClient
from wmca_proc import process_msg

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)


# Win32 스레드 내부 전용 커맨드 메시지
_WM_CONNECT    = win32con.WM_USER + 1
_WM_QUERY      = win32con.WM_USER + 2
_WM_ATTACH     = win32con.WM_USER + 3
_WM_DISCONNECT = win32con.WM_USER + 4


class WmcaHandler:
    def __init__(self, bridge):
        self.bridge = bridge
        self.client = WmcaClient()
        self.hwnd = None
        self._hwnd_ready = threading.Event()
        self._pending_call = None   # Win32 스레드가 실행할 callable
        self._call_lock = threading.Lock()
        self._thread = threading.Thread(target=self._msg_loop_thread)
        self._thread.daemon = True
        self._thread.start()

    def _post_to_win32(self, wm_cmd, fn):
        """fn을 Win32 스레드에서 실행하도록 예약하고 PostMessage로 깨운다."""
        with self._call_lock:
            self._pending_call = fn
        win32api.PostMessage(self.hwnd, wm_cmd, 0, 0)

    def _msg_loop_thread(self):
        """별도 스레드에서 윈도우 생성 및 메시지 펌프 실행"""
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = "WMCA_Handler_Window"
        wc.hInstance = win32api.GetModuleHandle(None)

        class_atom = win32gui.RegisterClass(wc)

        # 메시지 수신 전용 윈도우 생성 (보이지 않음)
        self.hwnd = win32gui.CreateWindow(
            class_atom, "WMCA_Hidden", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
        )
        self._hwnd_ready.set()

        # 메시지 루프 시작 (블로킹)
        win32gui.PumpMessages()

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        # Win32 스레드에서 DLL 함수를 직접 호출하는 커맨드 처리
        if msg in (_WM_CONNECT, _WM_QUERY, _WM_ATTACH, _WM_DISCONNECT):
            with self._call_lock:
                fn = self._pending_call
                self._pending_call = None
            if fn:
                fn()
            return 0
        return process_msg(self, hwnd, msg, wparam, lparam)

    async def wait_ready(self, timeout: float = 5.0) -> bool:
        """HWND가 생성될 때까지 비동기 대기"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self._hwnd_ready.wait(timeout)
        )

    def connect_server(self, user_id, user_pw, cert_pw):
        if not self.hwnd:
            self.bridge.add_message("핸들러 초기화 중입니다. 잠시 후 다시 시도하세요.")
            return

        def _do():
            print(f"[Win32 thread] wmcaConnect 호출 hwnd={self.hwnd}", flush=True)
            res = self.client.dll.wmcaConnect(
                self.hwnd,
                CA_WMCAEVENT,
                b'T', b'W',
                user_id.encode('cp949'),
                user_pw.encode('cp949'),
                cert_pw.encode('cp949')
            )
            print(f"[Win32 thread] wmcaConnect res={res}", flush=True)

        self._post_to_win32(_WM_CONNECT, _do)

    def query_price(self, code, market="UNT"):
        """현재가 조회 요청"""
        if not self.hwnd:
            return

        tr_code = f"IVWUTKMST04.{market}"
        in_block = TIVWUTKMST04In()
        ctypes.memset(ctypes.addressof(in_block), 0x20, ctypes.sizeof(in_block))
        in_block.form_lang = b'k'
        in_block.shrn_iscd = code.encode('cp949')

        def _do():
            res = self.client.dll.wmcaQuery(
                self.hwnd, TRID_IVWUTKMST04,
                tr_code.encode('cp949'),
                ctypes.cast(ctypes.byref(in_block), ctypes.c_char_p),
                ctypes.sizeof(in_block), 0
            )
            print(f"[Win32 thread] wmcaQuery(price) res={res}", flush=True)

        self._post_to_win32(_WM_QUERY, _do)

    def disconnect_server(self):
        """프로그램 종료 시 서버 연결 해제"""
        if not (self.client and self.client.dll and self.hwnd):
            return
        def _do():
            try:
                self.client.dll.wmcaDisconnect()
            except Exception as e:
                print(f"[Win32 thread] wmcaDisconnect 오류: {e}", flush=True)
        self._post_to_win32(_WM_DISCONNECT, _do)

    def attach_price(self, code, market="UNT"):
        """실시간 시세 구독"""
        if not self.hwnd:
            return

        code_b = code.strip().encode('cp949')
        def _do():
            res = self.client.dll.wmcaAttach(
                self.hwnd, b"mc", code_b, len(code_b), len(code_b)
            )
            print(f"[Win32 thread] wmcaAttach res={res}", flush=True)

        self._post_to_win32(_WM_ATTACH, _do)

    def query_balance(self, acc_index: int, acc_text: str, account_pwd: str):
        """주식 잔고조회 c8201"""
        if not self.hwnd:
            return

        in_block = Tc8201InBlock()
        ctypes.memset(ctypes.addressof(in_block), 0x20, ctypes.sizeof(in_block))
        out44 = (ctypes.c_char * 44)()
        ctypes.memset(ctypes.addressof(out44), 0x20, ctypes.sizeof(out44))
        self.client.dll.wmcaSetAccountNoPwd(
            out44, acc_text.encode("cp949"), account_pwd.encode("cp949")
        )
        in_block.pswd_noz8 = bytes(out44)
        in_block.bnc_bse_cdz1 = b"1"
        in_block.aet_bsez1 = b"1"
        in_block.qut_dit_cdz3 = b"000"

        def _do():
            res = self.client.dll.wmcaQuery(
                self.hwnd, TRID_C8201, b"c8201",
                ctypes.cast(ctypes.byref(in_block), ctypes.c_char_p),
                ctypes.sizeof(in_block), int(acc_index)
            )
            print(f"[Win32 thread] wmcaQuery(balance) res={res}", flush=True)

        self._post_to_win32(_WM_QUERY, _do)

    def sell_order(self, acc_index: int, account_pwd: str, order_pwd: str,
                   code: str, price: int, qty: int):
        """매도주문 c8101"""
        if not self.hwnd:
            return

        in_block = Tc8101InBlock()
        ctypes.memset(ctypes.addressof(in_block), 0x20, ctypes.sizeof(in_block))
        acc_out44 = (ctypes.c_char * 44)()
        ctypes.memset(ctypes.addressof(acc_out44), 0x20, ctypes.sizeof(acc_out44))
        self.client.dll.wmcaSetAccountIndexPwd(acc_out44, int(acc_index), account_pwd.encode("cp949"))
        ord_out44 = (ctypes.c_char * 44)()
        ctypes.memset(ctypes.addressof(ord_out44), 0x20, ctypes.sizeof(ord_out44))
        self.client.dll.wmcaSetOrderPwd(ord_out44, order_pwd.encode("cp949"))
        in_block.pswd_noz8 = bytes(acc_out44)
        in_block.issue_codez6 = code.encode("cp949")
        in_block.order_qtyz12 = f"{qty:012d}".encode("cp949")
        in_block.order_unit_pricez10 = f"{price:010d}".encode("cp949")
        in_block.trade_typez2 = b"00"
        in_block.shsll_pos_flagz1 = b"0"
        in_block.trad_pswd_no_1z8 = bytes(ord_out44)
        in_block.trad_pswd_no_2z8 = bytes(ord_out44)
        in_block.rmt_mkt_cdz3 = b"KRX"
        in_block.trde_dvsn_codez1 = b"1"

        def _do():
            res = self.client.dll.wmcaQuery(
                self.hwnd, TRID_C8101, b"c8101",
                ctypes.cast(ctypes.byref(in_block), ctypes.c_char_p),
                ctypes.sizeof(in_block), int(acc_index)
            )
            print(f"[Win32 thread] wmcaQuery(sell) res={res}", flush=True)

        self._post_to_win32(_WM_QUERY, _do)
