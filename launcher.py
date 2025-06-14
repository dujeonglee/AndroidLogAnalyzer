import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import http.server
import socketserver
import webbrowser
import os
import datetime
import queue
import time
import signal

class DebuggingHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def setup(self):
        print(f"[{time.time():.3f}] setup() 시작")
        super().setup()
        print(f"[{time.time():.3f}] setup() 완료")
    
    def handle(self):
        print(f"[{time.time():.3f}] handle() 시작 - HTTP 요청 처리")
        super().handle()
        print(f"[{time.time():.3f}] handle() 완료")
    
    def parse_request(self):
        print(f"[{time.time():.3f}] parse_request() 시작 - 데이터 수신 대기")
        result = super().parse_request()
        print(f"[{time.time():.3f}] parse_request() 완료")
        return result
    
    def do_GET(self):
        print(f"[{time.time():.3f}] do_GET() 시작 - 파일 처리")
        super().do_GET()
        print(f"[{time.time():.3f}] do_GET() 완료")

class DebuggingTCPServer(socketserver.TCPServer):
    def get_request(self):
        print(f"[{time.time():.3f}] get_request() 시작 - accept() 대기중...")
        sock, addr = self.socket.accept()
        print(f"[{time.time():.3f}] get_request() 완료 - 클라이언트 {addr} 연결됨")
        return sock, addr
    
    def handle_request(self):
        print(f"[{time.time():.3f}] handle_request() 시작")
        super().handle_request()
        print(f"[{time.time():.3f}] handle_request() 완료")

class WebServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Web Server")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 서버 관련 변수
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.server_port = None  # 실제 바인딩된 포트 저장
        self.server_stop_thread = None
        
        # 로그 큐 (스레드 간 안전한 통신용)
        self.log_queue = queue.Queue()
        
        self.setup_gui()
        self.setup_logging()
        
        # 주기적으로 로그 큐 확인
        self.root.after(100, self.process_log_queue)
        
    def setup_gui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 루트 창의 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 상단 컨트롤 패널
        control_frame = ttk.LabelFrame(main_frame, text="서버 컨트롤", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # 포트 설정
        ttk.Label(control_frame, text="포트:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar(value="8000")
        self.port_entry = ttk.Entry(control_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self.port_entry.config(state=tk.DISABLED)
        
        # 시작/정지 버튼
        self.start_button = ttk.Button(control_frame, text="Open Browser", command=self.open_browser)
        self.start_button.grid(row=0, column=2, padx=(0, 5))
        self.start_button.config(state=tk.DISABLED)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=(0, 10))
        
        # 상태 표시
        self.status_var = tk.StringVar(value="서버 정지됨")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground="red")
        self.status_label.grid(row=0, column=4, sticky=tk.W)
        
        # 서버 정보 표시
        info_frame = ttk.LabelFrame(main_frame, text="서버 정보", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="서빙 디렉토리:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.dir_var = tk.StringVar(value=os.getcwd())
        ttk.Label(info_frame, textvariable=self.dir_var, foreground="blue").grid(row=0, column=1, sticky=tk.W)
        
        # 콘솔 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="콘솔 로그", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 로그 텍스트 영역 (스크롤 가능)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        # 로그 클리어 버튼
        ttk.Button(log_frame, text="로그 클리어", command=self.clear_log).grid(row=1, column=0, sticky=tk.W)
        
    def setup_logging(self):
        """로그 시스템 초기화"""
        self.log("=" * 50)
        self.log("Simple Web Server 시작")
        self.log(f"현재 디렉토리: {os.getcwd()}")
        
        # index.html 파일 존재 확인
        index_path = os.path.join(os.getcwd(), "index.html")
        if os.path.exists(index_path):
            self.log("✓ index.html 파일 발견")
        else:
            self.log("⚠ index.html 파일이 없습니다. 기본 디렉토리 목록이 표시됩니다.")
        
        self.log("=" * 50)
    
    def log(self, message):
        """로그 메시지를 큐에 추가"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_queue.put(log_message)
    
    def process_log_queue(self):
        """로그 큐에서 메시지를 처리하여 GUI에 표시"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)  # 자동 스크롤
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        
        # 100ms 후에 다시 확인
        self.root.after(100, self.process_log_queue)
    
    def clear_log(self):
        """로그 텍스트 영역 클리어"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("로그가 클리어되었습니다.")
    
    def open_browser(self):
        """웹서버 시작"""
        # 브라우저 자동 열기
        try:
            browser_url = f"http://localhost:{self.server_port}"
            self.log(f"브라우저 열기 시도: {browser_url}")
            webbrowser.open(browser_url)
            self.log("✓ 브라우저 열기 성공")
        except Exception as e:
            self.log(f"⚠ 브라우저 열기 실패: {e}")

    def start_server(self):
        try:
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                raise ValueError("포트 범위는 1-65535입니다.")
        except ValueError as e:
            messagebox.showerror("오류", f"잘못된 포트 번호: {e}")
            return False
        
        if self.is_running:
            self.log("⚠ 서버가 이미 실행 중입니다.")
            return False
        
        # 서버 시작
        self.log(f"서버 시작 중... 요청된 포트: {port}")
        
        try:
            # 웹서버 생성 - 디버그 웹서버
            self.server = DebuggingTCPServer(("", port), DebuggingHTTPRequestHandler)
            
            # 실제 바인딩된 포트 확인 및 저장
            self.server_port = self.server.server_address[1]
            self.log(f"실제 바인딩된 포트: {self.server_port}")
            
            # 포트가 요청한 것과 다른지 확인
            if self.server_port != port:
                self.log(f"⚠ 요청한 포트({port})와 실제 포트({self.server_port})가 다릅니다!")
            else:
                self.log(f"✓ 포트 {port} 정상 바인딩됨")
            
            # 서버 상태를 먼저 True로 설정 (중요!)
            self.is_running = True
            
            # 별도 스레드에서 서버 실행
            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # GUI 상태 업데이트
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set(f"서버 실행 중 (포트: {self.server_port})")
            self.status_label.config(foreground="green")
            
            self.log(f"✓ 서버 시작 완료: http://localhost:{self.server_port}")

            self.open_browser()
            return True
        
        except OSError as e:
            self.log(f"✗ 서버 시작 실패: {e}")
            self.port_var.set(port+1)
            return False
            
    
    def run_server(self):
        """서버 실행 (별도 스레드)"""
        try:
            self.log("서버 스레드 시작됨")
            
            while self.is_running:
                try:
                    # handle_request는 하나의 요청만 처리 (블로킹)
                    self.server.handle_request()
                except OSError as e:
                    # 서버 소켓이 닫힌 경우
                    if not self.is_running:
                        self.log("서버 종료 신호 감지됨")
                        break
                    else:
                        self.log(f"⚠ 소켓 오류: {e}")
                        break
                        
        except Exception as e:
            if self.is_running:
                self.log(f"✗ 서버 스레드 오류: {e}")
        finally:
            self.log("서버 스레드 종료됨")

    def stop_server(self):
        """애플리케이션 종료"""
        os.kill(os.getpid(), signal.SIGTERM)
    
    def on_closing(self):
        """애플리케이션 종료"""
        os.kill(os.getpid(), signal.SIGTERM)

def main():
    root = tk.Tk()
    app = WebServerGUI(root)
    while True:
        if app.start_server():
            break
    # 창 닫기 이벤트 처리
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()