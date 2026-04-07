"""
wmca_proc.py
─────────────────────────────────────────────────────────────────────────────
Win32 메시지 디스패처 및 WMCA 응답 파서.

CA_WMCAEVENT (WM_USER+8400) 메시지를 wparam 값에 따라 분기하고,
lparam으로 전달된 OUTDATABLOCK 포인터에서 실제 데이터를 파싱합니다.

wparam 분기:
    CA_CONNECTED    (1134) — 로그인 성공, 계좌 목록 파싱
    CA_DISCONNECTED (1144) — 연결 끊김
    CA_RECEIVEDATA  (1234) — TR 조회 응답 (현재가, 잔고 등)
    CA_RECEIVESISE  (1244) — 실시간 시세 (체결/주문 통보)
    CA_RECEIVEMESSAGE (1254) — 서버 알림 메시지
    CA_RECEIVECOMPLETE (1264) — TR 응답 완료 → Future resolve
    CA_RECEIVEERROR (1274) — TR 오류 → Future reject
─────────────────────────────────────────────────────────────────────────────
"""

from trio_ord import *
from trio_inv import *
from wmca_def import *
import logging
import ctypes
import win32gui


def process_msg(handler, hwnd, msg, wparam, lparam):
    print(f"[MSG] hwnd={hwnd} msg={msg}(0x{msg:04X}) wp={wparam} lp={lparam}", flush=True)
    bridge = handler.bridge

    # 9424 (CA_WMCAEVENT) 메시지가 들어왔을 때
    if msg == CA_WMCAEVENT:
        # ---------------------------------------------------------
        # [D] 접속 끊김 (CA_DISCONNECTED = 1144)
        # ---------------------------------------------------------
        if wparam == CA_DISCONNECTED:
            print("🔌 연결 끊김 (CA_DISCONNECTED)")
            bridge.on_disconnected()
            return 0

        # ---------------------------------------------------------
        # [A] 로그인 성공 (CA_CONNECTED = 1134)
        # ---------------------------------------------------------
        elif wparam == CA_CONNECTED:
            print("🎉 로그인 성공! 데이터 파싱 시작...")
            try:
                login_block = ctypes.cast(lparam, ctypes.POINTER(LOGINBLOCK)).contents

                if login_block.pLoginInfo:
                    login_info = login_block.pLoginInfo.contents
                    logintime = login_info.szDate.decode('cp949').strip()
                    loginServer = login_info.szServerName.decode('cp949').strip()
                    user_id = login_info.szUserID.decode('cp949').strip()
                    count = login_info.get_count()

                    info_msg = (f"✅ {logintime}, {loginServer}, "
                                f"접속완료: ID={user_id}, 계좌수={count}")
                    logging.info(info_msg)

                    account_list = []
                    for i in range(count):
                        acc = login_info.accountlist[i]
                        acc_info = acc.get_info()
                        account_list.append(acc_info)
                        logging.info(
                            f"[계좌 {i+1}] {acc_info['계좌번호']} "
                            f"({acc_info['계좌명']}) - {acc_info['상품코드']}"
                        )

                    bridge.on_connected(account_list)

            except Exception as e:
                logging.error(f"⚠️ 로그인 정보 파싱 오류: {e}")
                print(f"⚠️ 로그인 정보 파싱 오류: {e}")
            return 0

        # ---------------------------------------------------------
        # [C] 데이터 수신 (CA_RECEIVEDATA = 1234)
        # ---------------------------------------------------------
        elif wparam == CA_RECEIVEDATA:
            print("📊 CA_RECEIVEDATA 데이터 수신 (Query 결과)")
            try:
                real_data_addr = ctypes.cast(lparam, ctypes.POINTER(OUTDATABLOCK)).contents

                if real_data_addr.TrIndex == TRID_IVWUTKMST04:
                    receive_data = ctypes.cast(
                        real_data_addr.pData, ctypes.POINTER(RECEIVED)
                    ).contents
                    print(f"CA_RECEIVEDATA: {real_data_addr.TrIndex}, {receive_data.szBlockName}")

                    if receive_data.szBlockName.decode('cp949').strip() == "IVWUTKMST04Out1":
                        raw_bytes = ctypes.string_at(receive_data.szData, receive_data.nLen)
                        struct_size = ctypes.sizeof(TIVWUTKMST04Out1)
                        pOut1 = TIVWUTKMST04Out1.from_buffer_copy(raw_bytes[:struct_size])

                        data = {
                            "종목코드": pOut1.shrn_iscd.decode("cp949", "ignore").strip(),
                            "시간":    pOut1.hoga_bsop_hour.decode("cp949", "ignore").strip(),
                            "현재가":  pOut1.stck_prpr.decode("cp949", "ignore").strip(),
                            "부호":    pOut1.prdy_vrss_sign.decode("cp949", "ignore").strip(),
                            "대비":    pOut1.prdy_vrss.decode("cp949", "ignore").strip(),
                            "시가":    pOut1.stck_oprc.decode("cp949", "ignore").strip(),
                            "고가":    pOut1.stck_hgpr.decode("cp949", "ignore").strip(),
                            "저가":    pOut1.stck_lwpr.decode("cp949", "ignore").strip(),
                            "거래량":  pOut1.acml_vol.decode("cp949", "ignore").strip(),
                        }
                        bridge.append_data(TRID_IVWUTKMST04, data)

                        print(
                            f"종목코드: {pOut1.shrn_iscd.decode('cp949').strip()} "
                            f"종목명: {pOut1.hts_isnm.decode('cp949').strip()} "
                            f"시간: {pOut1.hoga_bsop_hour.decode('cp949').strip()} "
                            f"현재가: {pOut1.stck_prpr.decode('cp949').strip()} "
                            f"거래량: {pOut1.acml_vol.decode('cp949').strip()}"
                        )

                    elif receive_data.szBlockName.decode('cp949').strip() == "IVWUTKMST04Out2":
                        raw_bytes = ctypes.string_at(receive_data.szData, receive_data.nLen)
                        struct_size = ctypes.sizeof(TIVWUTKMST04Out2)
                        n_occurs = receive_data.nLen // struct_size

                        for i in range(n_occurs):
                            offset = struct_size * i
                            pOut2 = TIVWUTKMST04Out2.from_buffer_copy(
                                raw_bytes[offset:offset + struct_size]
                            )
                            print(
                                f"{pOut2.bsop_hour.decode('cp949').strip()} "
                                f"{pOut2.stck_prpr.decode('cp949').strip()}원 "
                                f"{pOut2.cntg_vol.decode('cp949').strip()}주"
                            )

                    elif receive_data.szBlockName.decode('cp949').strip() == "IVWUTKMST04Out3":
                        print("IVWUTKMST04Out3")

                elif real_data_addr.TrIndex == TRID_C8201:
                    receive_data = ctypes.cast(
                        real_data_addr.pData, ctypes.POINTER(RECEIVED)
                    ).contents
                    print(f"CA_RECEIVEDATA: {real_data_addr.TrIndex}, {receive_data.szBlockName}")

                    if receive_data.szBlockName.decode('cp949').strip() == "c8201OutBlock":
                        raw_bytes = ctypes.string_at(receive_data.szData, receive_data.nLen)
                        struct_size = ctypes.sizeof(Tc8201OutBlock)
                        pOut1 = Tc8201OutBlock.from_buffer_copy(raw_bytes[:struct_size])
                        data = {
                            "구분":         "계좌",
                            "예수금":       pOut1.dpsit_amtz16.decode("cp949", "ignore").strip(),
                            "출금가능금액": pOut1.chgm_pos_amtz16.decode("cp949", "ignore").strip(),
                            "주문가능금액": pOut1.order_pos_csamtz16.decode("cp949", "ignore").strip(),
                            "평가금액":     pOut1.bal_ass_ttamtz16.decode("cp949", "ignore").strip(),
                            "순자산액":     pOut1.asset_tot_amtz16.decode("cp949", "ignore").strip(),
                            "총평가금액":   pOut1.tot_eal_plsz18.decode("cp949", "ignore").strip(),
                            "수익률":       pOut1.pft_rtz15.decode("cp949", "ignore").strip(),
                        }
                        bridge.append_data(TRID_C8201, data)

                    elif receive_data.szBlockName.decode('cp949').strip() == "c8201OutBlock1":
                        raw_bytes = ctypes.string_at(receive_data.szData, receive_data.nLen)
                        struct_size = ctypes.sizeof(Tc8201OutBlock1)
                        n_occurs = receive_data.nLen // struct_size

                        for i in range(n_occurs):
                            offset = struct_size * i
                            pOut1 = Tc8201OutBlock1.from_buffer_copy(
                                raw_bytes[offset:offset + struct_size]
                            )
                            data = {
                                "구분":     "잔고",
                                "종목코드": pOut1.issue_codez6.decode("cp949", "ignore").strip(),
                                "종목명":   pOut1.issue_namez40.decode("cp949", "ignore").strip(),
                                "잔고유형": pOut1.bal_typez6.decode("cp949", "ignore").strip(),
                                "잔고수량": pOut1.bal_qtyz16.decode("cp949", "ignore").strip(),
                            }
                            bridge.append_data(TRID_C8201, data)

                elif real_data_addr.TrIndex == TRID_C8101:
                    receive_data = ctypes.cast(
                        real_data_addr.pData, ctypes.POINTER(RECEIVED)
                    ).contents
                    print(f"CA_RECEIVEDATA: {real_data_addr.TrIndex}, {receive_data.szBlockName}")

            except Exception as e:
                print(f"⚠️ 데이터 파싱 오류: {e}")
            return 0

        # ---------------------------------------------------------
        # [B] 메시지 수신 (CA_RECEIVEMESSAGE = 1254)
        # ---------------------------------------------------------
        elif wparam == CA_RECEIVEMESSAGE:
            try:
                real_data_addr = ctypes.cast(lparam, ctypes.POINTER(OUTDATABLOCK)).contents
                receive_data = ctypes.cast(
                    real_data_addr.pData, ctypes.POINTER(RECEIVED)
                ).contents

                total_len = receive_data.nLen
                raw_bytes = ctypes.string_at(receive_data.szData, total_len)

                msg_cd = ""
                user_msg = ""
                if total_len >= 5:
                    msg_cd = raw_bytes[:5].decode('cp949', errors='ignore')
                    user_msg = raw_bytes[5:total_len].decode('cp949', errors='ignore').strip()

                logmsg = f"[CA_RECEIVEMESSAGE] {real_data_addr.TrIndex}, {msg_cd}, {user_msg}"
                bridge.add_message(logmsg)

            except Exception as e:
                bridge.add_message(f"⚠️ 메시지 파싱 오류: {e}")
            return 0

        # ---------------------------------------------------------
        # [E] 수신 완료 (CA_RECEIVECOMPLETE = 1264)
        # ---------------------------------------------------------
        elif wparam == CA_RECEIVECOMPLETE:
            try:
                real_data_addr = ctypes.cast(lparam, ctypes.POINTER(OUTDATABLOCK)).contents
                trid = real_data_addr.TrIndex

                receive_data = ctypes.cast(
                    real_data_addr.pData, ctypes.POINTER(RECEIVED)
                ).contents
                if receive_data.szBlockName:
                    logmsg = (f"[CA_RECEIVECOMPLETE] TRID={trid}, "
                              f"{receive_data.szBlockName}")
                    bridge.add_message(logmsg)

                # 해당 TRID의 future를 resolve
                bridge.complete_request(trid)

            except Exception as e:
                bridge.add_message(f"⚠️ RECEIVECOMPLETE 파싱 오류: {e}")
            return 0

        # ---------------------------------------------------------
        # [F] 실시간 시세 (CA_RECEIVESISE = 1244)
        # ---------------------------------------------------------
        elif wparam == CA_RECEIVESISE:
            try:
                real_data_addr = ctypes.cast(lparam, ctypes.POINTER(OUTDATABLOCK)).contents
                receive_data = ctypes.cast(
                    real_data_addr.pData, ctypes.POINTER(RECEIVED)
                ).contents

                total_len = receive_data.nLen
                raw_bytes = ctypes.string_at(receive_data.szData, total_len)

                trpart = raw_bytes[:2]
                value_part = raw_bytes[3:total_len]

                if trpart.decode('cp949').strip() == "mc":
                    mc_bytes = ctypes.string_at(value_part, total_len - 3)
                    struct_size = ctypes.sizeof(TmcOutBlock)
                    pOut1 = TmcOutBlock.from_buffer_copy(mc_bytes[:struct_size])
                    data = {
                        "종목코드": pOut1.code.decode("cp949", "ignore").strip(),
                        "시간":    pOut1.time.decode("cp949", "ignore").strip(),
                        "대비":    pOut1.change.decode("cp949", "ignore").strip(),
                        "가격":    pOut1.price.decode("cp949", "ignore").strip(),
                    }
                    bridge.add_realtime(data["종목코드"], data)

                elif trpart.decode('cp949').strip() == "d2":
                    d2_bytes = ctypes.string_at(value_part, total_len - 3)
                    struct_size = ctypes.sizeof(Td2OutBlock)
                    pOut1 = Td2OutBlock.from_buffer_copy(d2_bytes[:struct_size])
                    data = {
                        "구분":     "체결통보",
                        "ID":       pOut1.userid.decode("cp949", "ignore").strip(),
                        "계좌":     pOut1.accountno.decode("cp949", "ignore").strip(),
                        "주문번호": pOut1.orderno.decode("cp949", "ignore").strip(),
                        "주문구분": pOut1.slbygb.decode("cp949", "ignore").strip(),
                        "종목코드": pOut1.issuecd.decode("cp949", "ignore").strip(),
                        "종목명":   pOut1.issue_nm.decode("cp949", "ignore").strip(),
                        "수량":     pOut1.concgty.decode("cp949", "ignore").strip(),
                        "가격":     pOut1.concprc.decode("cp949", "ignore").strip(),
                        "시간":     pOut1.conctime.decode("cp949", "ignore").strip(),
                    }
                    bridge.add_realtime("d2_orders", data)

                elif trpart.decode('cp949').strip() == "d3":
                    d3_bytes = ctypes.string_at(value_part, total_len - 3)
                    struct_size = ctypes.sizeof(Td3OutBlock)
                    pOut1 = Td3OutBlock.from_buffer_copy(d3_bytes[:struct_size])
                    data = {
                        "구분":     "주문통보",
                        "ID":       pOut1.userid.decode("cp949", "ignore").strip(),
                        "계좌":     pOut1.accountno.decode("cp949", "ignore").strip(),
                        "주문번호": pOut1.orderno.decode("cp949", "ignore").strip(),
                        "주문구분": pOut1.slbygb.decode("cp949", "ignore").strip(),
                        "종목코드": pOut1.issuecd.decode("cp949", "ignore").strip(),
                        "종목명":   pOut1.issuename.decode("cp949", "ignore").strip(),
                        "수량":     pOut1.ordergty.decode("cp949", "ignore").strip(),
                        "가격":     pOut1.orderprc.decode("cp949", "ignore").strip(),
                        "시간":     pOut1.order_time.decode("cp949", "ignore").strip(),
                    }
                    bridge.add_realtime("d3_orders", data)

                else:
                    logmsg = (f"[CA_RECEIVESISE] {real_data_addr.TrIndex}, "
                              f"{receive_data.szBlockName}")
                    bridge.add_message(logmsg)

            except Exception as e:
                bridge.add_message(f"⚠️ RECEIVESISE 파싱 오류: {e}")
            return 0

        # ---------------------------------------------------------
        # [G] 오류 수신 (CA_RECEIVEERROR = 1274)
        # ---------------------------------------------------------
        elif wparam == CA_RECEIVEERROR:
            try:
                real_data_addr = ctypes.cast(lparam, ctypes.POINTER(OUTDATABLOCK)).contents
                receive_data = ctypes.cast(
                    real_data_addr.pData, ctypes.POINTER(RECEIVED)
                ).contents

                total_len = receive_data.nLen
                raw_bytes = ctypes.string_at(receive_data.szData, total_len)

                msg_cd = ""
                user_msg = ""
                if total_len >= 5:
                    msg_cd = raw_bytes[:5].decode('cp949', errors='ignore')
                    user_msg = raw_bytes[5:total_len].decode('cp949', errors='ignore').strip()

                bridge.add_error_message(real_data_addr.TrIndex, msg_cd, user_msg)

            except Exception as e:
                bridge.add_message(f"⚠️ RECEIVEERROR 파싱 오류: {e}")
            return 0

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
