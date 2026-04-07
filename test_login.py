"""
로그인 테스트 - 순수 스레드 방식 (asyncio 없음)
실행: py -3.13-32 test_login.py
"""
import threading
import getpass
import time
from wmca_bridge import WmcaBridge
from wmca_handler import WmcaHandler

user_id = input("ID: ")
user_pw = getpass.getpass("비밀번호: ")
cert_pw = getpass.getpass("인증서 비밀번호: ")

# ---------------------------------------------------------------
# 브리지: asyncio 없이 threading.Event 로 대기
# ---------------------------------------------------------------
bridge = WmcaBridge()
# bridge.loop = None  → call_soon_threadsafe 안 씀, 직접 이벤트로 대기

login_event = threading.Event()
login_result = [None]  # [accounts_list or error_string]

_orig_on_connected = bridge.on_connected
def _on_connected(accounts):
    bridge.accounts   = accounts
    bridge.is_connected = True
    login_result[0] = ("ok", accounts)
    login_event.set()
bridge.on_connected = _on_connected

_orig_on_disconnected = bridge.on_disconnected
def _on_disconnected():
    _orig_on_disconnected()
    if not login_event.is_set():
        login_result[0] = ("disconnect", "CA_DISCONNECTED 수신")
        login_event.set()
bridge.on_disconnected = _on_disconnected

_orig_add_message = bridge.add_message
def _add_message(msg):
    bridge.messages.appendleft(msg)
    print(f"  [BRIDGE MSG] {msg}", flush=True)
    # login 완료 판단: 처리중/진행중 메시지는 무시, 실제 오류만 종료
    if not login_event.is_set() and ("처리중" not in msg) and ("오류" in msg or "ERROR" in msg or "접속 실패" in msg or "CA_RECEIVEERROR" in msg):
        login_result[0] = ("message", msg)
        login_event.set()
bridge.add_message = _add_message

_orig_add_error = bridge.add_error_message
def _add_error(trid, msg_cd, user_msg):
    bridge.add_message(f"[CA_RECEIVEERROR] trid={trid} code={msg_cd} msg={user_msg}")
    if not login_event.is_set():
        login_result[0] = ("error", f"[{msg_cd}] {user_msg}")
        login_event.set()
bridge.add_error_message = _add_error

# ---------------------------------------------------------------
# 핸들러 시작
# ---------------------------------------------------------------
print("WmcaHandler 초기화 중...", flush=True)
handler = WmcaHandler(bridge)

if not handler._hwnd_ready.wait(5):
    print("[ERROR] HWND 생성 타임아웃")
    exit(1)
print(f"HWND 준비: {handler.hwnd}", flush=True)

handler.connect_server(user_id, user_pw, cert_pw)
print("접속 요청 전송. 60초 대기...\n", flush=True)

# ---------------------------------------------------------------
# 대기 & 진행 상황 출력
# ---------------------------------------------------------------
for i in range(60):
    if login_event.wait(timeout=1):
        break
    if (i + 1) % 5 == 0:
        print(f"  [{i+1}초 경과] 메시지 버퍼: {list(bridge.messages)}", flush=True)

# ---------------------------------------------------------------
# 결과 출력
# ---------------------------------------------------------------
print("\n=== 결과 ===")
if not login_event.is_set():
    print("60초 타임아웃 - 아무 응답 없음")
    print("브리지 메시지:", list(bridge.messages))
else:
    kind, data = login_result[0]
    if kind == "ok":
        print(f"로그인 성공! 계좌 수: {len(data)}")
        for i, acc in enumerate(data):
            print(f"  [{i}] {acc['계좌번호']} {acc['계좌명']} ({acc['상품코드']})")
    else:
        print(f"로그인 실패 ({kind}): {data}")
        print("전체 메시지:", list(bridge.messages))
