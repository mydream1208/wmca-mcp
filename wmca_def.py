"""
wmca_def.py
─────────────────────────────────────────────────────────────────────────────
WMCA 공통 상수 및 기본 ctypes 구조체 정의.

구조체 작성 규칙:
    - _pack_ = 1        : 1바이트 정렬 (DLL 전문 규격 필수)
    - 0x20 초기화       : 입력 블록은 memset(0x20)으로 공백 초기화
    - cp949 인코딩      : 모든 문자열 인코딩/디코딩에 cp949 사용
    - _fieldname 접미사 : 전문 구분자용 1바이트 패딩 필드
─────────────────────────────────────────────────────────────────────────────
"""

from ctypes import *

# ------------------------------------------------------------------
# 상수 정의
# ------------------------------------------------------------------
# 메시지 상수
WM_USER = 0x0400
CA_WMCAEVENT        = WM_USER + 8400  # (1024+8400 = 9424)
# 응답 메시지 ID
CA_CONNECTED        = WM_USER + 110 # 1024+110 = 1134
CA_DISCONNECTED     = WM_USER + 120 # 1024+120 = 1144
CA_SOCKETERROR      = WM_USER + 130 # 1024+130 = 1154
CA_RECEIVEDATA      = WM_USER + 210 # 1024+210 = 1234
CA_RECEIVESISE      = WM_USER + 220 # 1024+220 = 1244
CA_RECEIVEMESSAGE   = WM_USER + 230 # 1024+230 = 1254
CA_RECEIVECOMPLETE  = WM_USER + 240 # 1024+240 = 1264
CA_RECEIVEERROR     = WM_USER + 250 # 1024+250 = 1274

# USER 상수 추가 (임의 지정)
TRID_IVWUTKMST04 = 4000  # 현재가 조회용 ID
TRID_C8201  = 5000 # 잔고조회용
TRID_C8101  = 6000 # 매도 주문용

# ------------------------------------------------------------------
# 데이터 메세지 구조체 [C++] MSGHEADER
# ------------------------------------------------------------------
class MSGHEADER(Structure):
    _pack_ = 1
    _fields_ = [
        ("msg_cd",      c_char * 5),
        ("user_msg",    c_char * 80),
    ]
    
    def get_text(self):
        return safe_decode(self.user_msg)
    def get_code(self):
        return safe_decode(self.msg_cd)

# ------------------------------------------------------------------
# 데이터 수신 구조체 (RECEIVED & OUTDATABLOCK)
# ------------------------------------------------------------------
class RECEIVED(Structure):
    _pack_ = 1
    _fields_ = [
        ("szBlockName", c_char_p),  # 블록 이름 (char*)
        ("szData",      c_char_p),  # 실제 데이터 (char*)
        ("nLen",        c_int),     # 데이터 길이
    ]

class OUTDATABLOCK(Structure):
    _pack_ = 1
    _fields_ = [
        ("TrIndex", c_int),             # 요청 시 보낸 ID
        ("pData",   POINTER(RECEIVED)), # 수신 데이터 포인터
    ]

# [도우미 함수] 안전하게 문자열 디코딩 (Null 문자 제거 + 에러 무시)
def safe_decode(bytes_val):
    try:
        # 1. 바이너리에서 Null(\x00) 제거
        clean_bytes = bytes_val.split(b'\x00')[0]
        # 2. CP949 디코딩 (에러 발생 시 무시하고 넘어감)
        return clean_bytes.decode('cp949', errors='ignore').strip()
    except:
        return ""


# ------------------------------------------------------------------
# 데이터 로그인/계좌 구조체 [C++] ACCOUNTINFO
# ------------------------------------------------------------------
class ACCOUNTINFO(Structure):
    _pack_ = 1  # [필수] 1바이트 정렬
    _fields_ = [
        ("szAccountNo",     c_char * 11),
        ("szAccountName",   c_char * 40),
        ("act_pdt_cdz3",    c_char * 3),
        ("amn_tab_cdz4",    c_char * 4),
        ("expr_datez8",     c_char * 8),
        ("granted",         c_char),
        ("filler",          c_char * 189),
    ]

    def get_info(self):
        # safe_decode 함수를 사용하여 에러 방지
        return {
            "계좌번호": safe_decode(self.szAccountNo),
            "계좌명":   safe_decode(self.szAccountName),
            "상품코드": safe_decode(self.act_pdt_cdz3)
        }

# [C++] LOGININFO
class LOGININFO(Structure):
    _pack_ = 1
    _fields_ = [
        ("szDate",          c_char * 14),
        ("szServerName",    c_char * 15),
        ("szUserID",        c_char * 8),
        ("szAccountCount",  c_char * 3),
        ("accountlist",     ACCOUNTINFO * 999), # 배열
    ]
   
    def get_count(self):
        # 숫자로 변환
        val = safe_decode(self.szAccountCount)
        return int(val) if val.isdigit() else 0


# [C++] LOGINBLOCK
class LOGINBLOCK(Structure):
    _pack_ = 1
    _fields_ = [
        ("TrIndex",     c_int),
        ("pLoginInfo",  POINTER(LOGININFO))
    ]

# ------------------------------------------------------------------
# d2 - 실시간 주문 체결통보 (구분자 없음)
# ------------------------------------------------------------------
class Td2OutBlock(Structure):
    _pack_ = 1
    _fields_ = [
        ("userid", c_char * 8),
        ("itemgb", c_char * 1),
        ("accountno", c_char * 11),
        ("orderno", c_char * 10),
        ("issuecd", c_char * 15),
        ("slbygb", c_char * 1),
        ("concgty", c_char * 10),
        ("concprc", c_char * 11),
        ("conctime", c_char * 6),
        ("ucgb", c_char * 1),
        ("rejgb", c_char * 1),
        ("fundcode", c_char * 3),
        ("sin_gb", c_char * 2),
        ("loan_date", c_char * 8),
        ("ato_ord_tpe_chg", c_char * 1),
        ("issue_nm", c_char * 20),
        ("rmt_mkt_cd", c_char * 1),
        ("snd_mkt_cd", c_char * 1),
        ("ord_cond_prc", c_char * 11),
        ("sor_orrgb", c_char * 1),
        ("stop_efforn_gb", c_char * 1),
    ]


# ------------------------------------------------------------------
# d3 - 실시간 주문 통보 (구분자 없음)
# ------------------------------------------------------------------
class Td3OutBlock(Structure):
    _pack_ = 1
    _fields_ = [
        ("userid", c_char * 8),
        ("itemgb", c_char * 1),
        ("accountno", c_char * 11),
        ("orderno", c_char * 10),
        ("orgordno", c_char * 10),
        ("ordercd", c_char * 2),
        ("issuecd", c_char * 15),
        ("issuename", c_char * 20),
        ("slbygb", c_char * 1),
        ("order_type", c_char * 2),
        ("ordergty", c_char * 10),
        ("orderprc", c_char * 11),
        ("procnm", c_char * 2),
        ("commcd", c_char * 2),
        ("order_cond", c_char * 1),
        ("fundcode", c_char * 3),
        ("sin_gb", c_char * 2),
        ("order_time", c_char * 6),
        ("loan_date", c_char * 8),
        ("rmt_mkt_cd", c_char * 1),
        ("snd_mkt_cd", c_char * 1),
        ("ord_cond_prc", c_char * 11),
        ("sor_orrgb", c_char * 1),
        ("mkt_order_qty", c_char * 10),
    ]


