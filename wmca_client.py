"""
wmca_client.py
─────────────────────────────────────────────────────────────────────────────
WMCA DLL 로더 및 ctypes 함수 바인딩.

wmca.dll과 의존 DLL들은 mcp_server.py와 같은 디렉터리에 있어야 합니다.
_bind()에서 argtypes/restype을 명시하지 않으면 잘못된 호출 규약으로
프로세스가 크래시될 수 있으므로 반드시 바인딩합니다.
─────────────────────────────────────────────────────────────────────────────
"""

import ctypes
import os
from ctypes import POINTER, c_char
from ctypes import c_bool, c_void_p, c_uint32, c_char, c_char_p, c_int
from ctypes import wintypes

class WmcaClient:
    def __init__(self):
        # 현재 파일(wmca_client.py)이 있는 폴더 경로 (프로젝트 루트)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # dll_path를 'bin' 없이 현재 폴더로 지정
        dll_path = os.path.join(base_path, 'wmca.dll')

        print(f"DLL 로드 시도: {dll_path}")
        try:
            self.dll = ctypes.WinDLL(dll_path)
            print("[OK] DLL 로드 성공!")
            self._bind()
        except FileNotFoundError:
            print("[오류] wmca.dll을 찾을 수 없습니다. 경로를 확인하세요.")
            raise
        except OSError as e:
            print(f"[오류] DLL 로드 실패 (의존성 문제 가능성): {e}")
            raise

    def _bind(self):
        """DLL 함수들의 인자 타입과 리턴 타입을 명시 (Crash 방지용 안전장치)"""
        
        # 1) wmcaConnect: ID/PW/CertPW 로그인 (인자 7개)
        # BOOL wmcaConnect(HWND, DWORD, char, char, char*, char*, char*)
        try:
            print(f"wmcaConnect 함수 bind 호출")
            self.dll.wmcaConnect.restype = c_int
            self.dll.wmcaConnect.argtypes = [
                c_void_p,   # hWnd
                c_uint32,   # msg
                c_char,     # MediaType
                c_char,     # UserType
                c_char_p,   # ID
                c_char_p,   # PW
                c_char_p    # CertPW
            ]
        except AttributeError:
            print("[경고] wmcaConnect 함수를 찾을 수 없습니다.")

        # 2) wmcaConnectCert: 인증서 위치 로그인 (인자 5개) - SDK 문서 기준
        # BOOL wmcaConnectCert(HWND, DWORD, char, char, int)
        try:
            self.dll.wmcaConnectCert.restype = c_int
            self.dll.wmcaConnectCert.argtypes = [
                c_void_p, c_uint32, c_char, c_char, c_int
            ]
        except AttributeError:
            print("[경고] wmcaConnectCert 함수를 찾을 수 없습니다.")

        # 3) wmcaQuery: 조회
        try:
            self.dll.wmcaQuery.restype = c_int
            self.dll.wmcaQuery.argtypes = [c_void_p, c_int, c_char_p, c_char_p, c_int, c_int]
        except AttributeError: pass

        # 4) wmcaDisconnect: 연결 해제
        try:
            self.dll.wmcaDisconnect.restype = c_int
            self.dll.wmcaDisconnect.argtypes = []
        except AttributeError: pass

        # [5] wmcaDetachAll (실시간 해제)
        try:
            self.dll.wmcaDetachAll.argtypes = [c_void_p] # HWND
            self.dll.wmcaDetachAll.restype = None
        except AttributeError:
            pass

        # BOOL wmcaAttach(HWND, const char*, const char*, int, int)
        self.dll.wmcaAttach.restype = c_bool
        self.dll.wmcaAttach.argtypes = [c_void_p, c_char_p, c_char_p, c_int, c_int]

        # BOOL wmcaDetach(HWND, const char*, const char*, int, int)
        self.dll.wmcaDetach.restype = c_bool
        self.dll.wmcaDetach.argtypes = [c_void_p, c_char_p, c_char_p, c_int, c_int]

        # BOOL wmcaSetAccountIndexPwd(char* out44, int accIndex, const char* pwd)
        self.dll.wmcaSetAccountIndexPwd.restype = c_bool
        self.dll.wmcaSetAccountIndexPwd.argtypes = [POINTER(c_char), c_int, c_char_p]

        #BOOL wmcaSetAccountNoPwd(char* out44, const char* pszAccountNo, const char* pszPassword)
        self.dll.wmcaSetAccountNoPwd.restype = c_bool
        self.dll.wmcaSetAccountNoPwd.argtypes = [POINTER(c_char), c_char_p, c_char_p]

        # BOOL wmcaSetOrderPwd(char* out44, const char* pwd)
        self.dll.wmcaSetOrderPwd.restype = c_bool
        self.dll.wmcaSetOrderPwd.argtypes = [POINTER(c_char), c_char_p]

