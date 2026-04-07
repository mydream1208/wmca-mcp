import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from wmca_handler import WmcaHandler
from datetime import datetime
import logging

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO,  # <--- 이 부분이 핵심! (기본값은 WARNING)
    datefmt='%H:%M:%S'
)

                        
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WMCA 파이썬 클라이언트")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        # 핸들러 생성 및 시그널 연결
        self.wmca = WmcaHandler()
        self.wmca.sig_connected.connect(self.on_connected)
        self.wmca.sig_msg.connect(self.log)
        self.wmca.sig_error.connect(self.log)
        self.wmca.sig_update_accounts.connect(self.update_combo_box)
        self.wmca.sig_price_data.connect(self.on_price_data_received)
        self.wmca.sig_hoga_data.connect(self.on_realtime)
        self.wmca.sig_balance_data.connect(self.on_balance_data_received)

        self.init_ui()

    def init_ui(self):
        widget = QtWidgets.QWidget()
        root = QtWidgets.QGridLayout()
        root.setContentsMargins(10, 10, 10, 10)
        root.setHorizontalSpacing(10)
        root.setVerticalSpacing(10)
        
        # -----------------------------
        # 왼쪽 상단: 로그인
        # -----------------------------
        gb_login = QtWidgets.QGroupBox("로그인")
        login_form = QtWidgets.QFormLayout()

        self.input_id = QtWidgets.QLineEdit("mydream5")
        self.input_pw = QtWidgets.QLineEdit("sbpark!1")
        self.input_pw.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_cert = QtWidgets.QLineEdit("sbpark!@12")
        self.input_cert.setEchoMode(QtWidgets.QLineEdit.Password)

        self.btn_login = QtWidgets.QPushButton("로그인")
        self.btn_login.clicked.connect(self.try_login)

        login_form.addRow("ID", self.input_id)
        login_form.addRow("PW", self.input_pw)
        login_form.addRow("공인인증 PW", self.input_cert)
        login_form.addRow(self.btn_login)
        gb_login.setLayout(login_form)

        # -----------------------------
        # 왼쪽 중간: 계좌번호 / 종목코드
        # -----------------------------
        gb_input = QtWidgets.QGroupBox("계좌 / 종목")
        input_form = QtWidgets.QFormLayout()

        self.combo_acc = QtWidgets.QComboBox()
        #계좌비번
        self.input_acc_pwd = QtWidgets.QLineEdit("1103")
        self.input_acc_pwd.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_acc_pwd.setPlaceholderText("계좌 비밀번호")

        #거래비번
        self.input_order_pwd = QtWidgets.QLineEdit("park1103")
        self.input_order_pwd.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_order_pwd.setPlaceholderText("거래 비밀번호")

        self.input_code = QtWidgets.QLineEdit("005930")
        self.input_code.setPlaceholderText("종목코드 6자리")

        self.input_price = QtWidgets.QLineEdit("300000")
        self.input_price.setPlaceholderText("주문가격")

        self.input_qty = QtWidgets.QLineEdit("1")
        self.input_qty.setPlaceholderText("주문수량")

        input_form.addRow("계좌번호", self.combo_acc)
        input_form.addRow("계좌비밀번호", self.input_acc_pwd)
        input_form.addRow("거래비밀번호", self.input_order_pwd)
        input_form.addRow("종목코드", self.input_code)
        input_form.addRow("주문가격", self.input_price)
        input_form.addRow("주문수량", self.input_qty)
        gb_input.setLayout(input_form)

        # -----------------------------
        # 왼쪽 하단: 버튼 영역
        # -----------------------------
        gb_action = QtWidgets.QGroupBox("실행")
        action_layout = QtWidgets.QVBoxLayout()

        self.btn_query = QtWidgets.QPushButton("현재가 조회")
        self.btn_query.clicked.connect(self.try_query)

        self.btn_realtime = QtWidgets.QPushButton("실시간 시세 수신")
        self.btn_realtime.clicked.connect(self.try_realtime)

        self.btn_balance = QtWidgets.QPushButton("잔고조회")
        self.btn_balance.clicked.connect(self.try_balance)

        self.btn_buy = QtWidgets.QPushButton("매수주문")
        self.btn_buy.clicked.connect(self.try_buy_order)

        self.btn_sell = QtWidgets.QPushButton("매도주문")
        self.btn_sell.clicked.connect(self.try_sell_order)

        action_layout.addWidget(self.btn_query)
        action_layout.addWidget(self.btn_realtime)
        action_layout.addWidget(self.btn_balance)
        action_layout.addWidget(self.btn_buy)
        action_layout.addWidget(self.btn_sell)
        action_layout.addStretch(1)
        gb_action.setLayout(action_layout)

        # -----------------------------
        # 오른쪽 상단: 로그
        # -----------------------------
        gb_log = QtWidgets.QGroupBox("로그")
        log_layout = QtWidgets.QVBoxLayout()

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        log_layout.addWidget(self.log_view)
        gb_log.setLayout(log_layout)

        # -----------------------------
        # 오른쪽 중간: 잔고조회 결과
        # -----------------------------
        gb_balance = QtWidgets.QGroupBox("잔고조회 결과")
        balance_layout = QtWidgets.QVBoxLayout()

        self.balance_view = QtWidgets.QTextEdit()
        self.balance_view.setReadOnly(True)

        balance_layout.addWidget(self.balance_view)
        gb_balance.setLayout(balance_layout)

        # -----------------------------
        # 오른쪽 하단: 현재가 + 호가
        # -----------------------------
        gb_price = QtWidgets.QGroupBox("현재가 + 호가")
        price_layout = QtWidgets.QVBoxLayout()

        self.price_view = QtWidgets.QTextEdit()
        self.price_view.setReadOnly(True)
        self.price_view.setMaximumHeight(180)

        self.hoga_view = QtWidgets.QTextEdit()
        self.hoga_view.setReadOnly(True)
        self.hoga_view.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        price_layout.addWidget(QtWidgets.QLabel("현재가"))
        price_layout.addWidget(self.price_view)
        price_layout.addWidget(QtWidgets.QLabel("호가"))
        price_layout.addWidget(self.hoga_view)
        gb_price.setLayout(price_layout)

        # -----------------------------
        # 전체 격자 배치
        # -----------------------------
        root.addWidget(gb_login,   0, 0)
        root.addWidget(gb_input,   1, 0)
        root.addWidget(gb_action,  2, 0)

        root.addWidget(gb_log,     0, 1)
        root.addWidget(gb_balance, 1, 1)
        root.addWidget(gb_price,   2, 1)

        # 비율 조정
        root.setColumnStretch(0, 2)
        root.setColumnStretch(1, 8)

        root.setRowStretch(0, 3)
        root.setRowStretch(1, 2)
        root.setRowStretch(2, 5)

        widget.setLayout(root)
        self.setCentralWidget(widget)

    def log(self, msg):
        self.log_view.append(str(msg))

    def try_login(self):
        uid = self.input_id.text()
        upw = self.input_pw.text()
        cpw = self.input_cert.text()
        
        self.log("접속 시도 중...")
        res = self.wmca.connect_server(uid, upw, cpw)
        if res == 1:
            self.log("요청 전송 완료 (응답 대기)")
        else:
            self.log(f"요청 실패: {res}")

    def on_connected(self):
        self.log("✅ app  " \
        "로그인 성공! 이제 조회할 수 있습니다.")

    def try_query(self):
        code = self.input_code.text().strip()
        if not code:
            self.log("⚠️ 종목코드를 입력해주세요.")
            return
        
        # UNT KRX NXT
        res = self.wmca.query_price(code, market="UNT")
    
    def try_realtime(self):
        code = self.input_code.text().strip()
        if not code:
            self.log("⚠️ 종목코드를 입력해주세요.")
            return
        res = self.wmca.attach_price(code, market="UNT")


    def on_price_data_received(self, data: dict):
        """핸들러에서 시세 데이터가 오면 호출됨"""
        lines = []
        for k in ["종목코드", "시간", "현재가", "부호", "대비", "시가", "고가", "저가", "거래량"]:
            if k in data:
                lines.append(f"{k}: {data[k]}")
        if not lines:
        # 예상 키가 없으면 전체 dump
            lines = [str(data)]

        self.price_view.append(" | ".join(lines))

        scrollbar = self.balance_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_realtime(self, data: dict):
        lines = []
        for k in ["종목코드", "시간", "대비", "가격"]:
            if k in data:
                lines.append(f"{k}: {data[k]}")
        if not lines:
        # 예상 키가 없으면 전체 dump
            lines = [str(data)]

        self.hoga_view.append(" | ".join(lines))

        scrollbar = self.hoga_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_balance_data_received(self, data: dict):
        now = datetime.now().strftime('%H:%M:%S')
        kind = data.get("구분", "")
        if kind == "잔고":
            prefix = "[잔고]"
            fields = ["종목코드", "종목명", "잔고유형", "잔고수량"]
        elif kind == "체결":
            prefix = "[체결]"
            fields = ["계좌", "주문번호", "주문구분","종목코드", "종목명", "수량", "가격", "시간"]
        elif kind == "계좌":
            prefix = "[계좌]"
            fields = ["예수금", "출금가능금액", "주문가능금액", "평가금액", "순자산액", "총평가금액", "수익률"]
        else:
            prefix = "[기타]"
            fields = list(data.keys())
        values = [f"[{now}] {prefix}"]
        for k in fields:
            if k in data:
                values.append(f"{k}: {data[k]}")

        if not values:
        # 예상 키가 없으면 전체 dump
            values = [str(data)]

        self.balance_view.append(" | ".join(values))

        scrollbar = self.balance_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        print("프로그램을 종료합니다.") 
        # 1. 서버 연결 끊기 (wmcaDisconnect)
        if hasattr(self, 'wmca'):
            self.wmca.disconnect_server()
        # 2. (선택사항) 스레드 정리 등 추가 작업
        # 3. 종료 승인
        event.accept()
        
    def update_combo_box(self, account_list):
        self.combo_acc.clear() # 기존 항목 삭제
        
        if not account_list:
            self.log("⚠️ 수신된 계좌가 없습니다.")
            return

        self.log(f"📋 계좌 {len(account_list)}개를 콤보박스에 추가합니다.")
        
        for acc in account_list:
            # 콤보박스에 "계좌번호 (계좌명)" 형태로 표시
            display_text = f"{acc['계좌번호']} ({acc['계좌명']})"
            
            # 실제 값으로는 계좌번호만 저장 (나중에 조회할 때 쓰기 편함)
            self.combo_acc.addItem(display_text, acc['계좌번호'])
    
    def try_balance(self):
        acc_index = self.combo_acc.currentIndex()+1
        acc_text = self.combo_acc.currentText()
        account_pwd = self.input_acc_pwd.text().strip()

        if acc_index < 0:
            self.log("?? 계좌를 선택해주세요.")
            return

        if not account_pwd:
            self.log("?? 계좌비밀번호를 입력해주세요.")
            return

        res = self.wmca.query_balance(acc_index, acc_text, account_pwd)
        self.log(f"잔고조회 요청 결과: {res}")
    
    def try_sell_order(self):
        acc_index = self.combo_acc.currentIndex()+1
        account_pwd = self.input_acc_pwd.text().strip()
        order_pwd = self.input_order_pwd.text().strip()
        code = self.input_code.text().strip()
        price = self.input_price.text().strip()
        qty = self.input_qty.text().strip()

        if acc_index < 0:
            self.log("?? 계좌를 선택해주세요.")
            return

        if not account_pwd:
            self.log("?? 계좌비밀번호를 입력해주세요.")
            return
        
        if not order_pwd:
            self.log("?? 거래비밀번호를 입력해주세요.")
            return

        if not code or len(code) != 6:
            self.log("?? 종목코드는 6자리여야 합니다.")
            return

        if not price.isdigit():
            self.log("?? 주문가격은 숫자여야 합니다.")
            return

        if not qty.isdigit():
            self.log("?? 주문수량은 숫자여야 합니다.")
            return

        res = self.wmca.sell_order(
            acc_index=acc_index,
            account_pwd=account_pwd,
            order_pwd=order_pwd,
            code=code,
            price=int(price),
            qty=int(qty),
        )
        self.log(f"매도주문 요청 결과: {res}")

    def try_buy_order(self):
        self.log("매수주문은 아직 미구현입니다.")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())