#!/usr/bin/env python3
import os
import sys
import http.server
import socketserver
import webbrowser
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import socket
import struct

class WebServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HTML 웹 서버 런처")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # 웹 서버 관련 변수
        self.httpd = None
        self.server_thread = None
        self.is_running = False
        self.port = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 제목
        title_label = tk.Label(
            self.root, 
            text="🌐 HTML 웹 서버 런처", 
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
        # 현재 디렉토리 표시
        self.dir_label = tk.Label(
            self.root,
            text=f"📁 현재 디렉토리: {os.getcwd()}",
            font=("Arial", 10),
            wraplength=450,
            justify="left"
        )
        self.dir_label.pack(pady=5)
        
        # HTML 파일 목록 표시
        self.files_frame = tk.Frame(self.root)
        self.files_frame.pack(pady=10, fill="x", padx=20)
        
        self.update_file_list()
        
        # 상태 표시
        self.status_label = tk.Label(
            self.root,
            text="⏹️ 서버 중지됨",
            font=("Arial", 12, "bold"),
            fg="red"
        )
        self.status_label.pack(pady=10)
        
        # URL 표시 (서버 실행 시)
        self.url_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10),
            fg="blue",
            cursor="hand2"
        )
        self.url_label.pack(pady=5)
        
        # 버튼 프레임
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        # Start 버튼
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Start Server",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            command=self.start_server
        )
        self.start_button.pack(side="left", padx=10)
        
        # Stop 버튼
        self.stop_button = tk.Button(
            button_frame,
            text="🛑 Stop Server",
            font=("Arial", 12, "bold"),
            bg="#f44336",
            fg="white",
            padx=20,
            pady=10,
            command=self.stop_server,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=10)
        
        # 고급 브라우저 제어 버튼 추가
        advanced_frame = tk.Frame(self.root)
        advanced_frame.pack(pady=10)
        
        # 중지 페이지 생성 버튼 (실험적 기능)
        stop_page_button = tk.Button(
            advanced_frame,
            text="🔄 중지 페이지로 이동",
            font=("Arial", 10),
            command=self.navigate_to_stop_page,
            state="disabled"
        )
        stop_page_button.pack(side="left", padx=5)
        self.stop_page_button = stop_page_button
        
        # URL 클릭 이벤트
        self.url_label.bind("<Button-1>", self.open_browser)
        
        # 윈도우 닫기 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def update_file_list(self):
        """HTML 파일 목록 업데이트"""
        # 기존 위젯 제거
        for widget in self.files_frame.winfo_children():
            widget.destroy()
            
        # HTML 파일 찾기
        html_files = list(Path.cwd().glob("*.html")) + list(Path.cwd().glob("*.htm"))
        
        files_label = tk.Label(
            self.files_frame,
            text="📋 HTML 파일 목록:",
            font=("Arial", 10, "bold")
        )
        files_label.pack(anchor="w")
        
        if html_files:
            for html_file in html_files:
                file_label = tk.Label(
                    self.files_frame,
                    text=f"   • {html_file.name}",
                    font=("Arial", 9)
                )
                file_label.pack(anchor="w")
        else:
            no_files_label = tk.Label(
                self.files_frame,
                text="   ⚠️ HTML 파일이 없습니다.",
                font=("Arial", 9),
                fg="orange"
            )
            no_files_label.pack(anchor="w")
    
    def find_index_file(self):
        """index.html 파일 찾기"""
        current_dir = Path.cwd()
        index_file = current_dir / "index.html"
        return index_file if index_file.exists() else None
    
    def find_available_port(self, start_port=8000):
        """사용 가능한 포트 찾기"""
        for port in range(start_port, start_port + 100):
            try:
                # 포트 사용 가능 여부 체크
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('localhost', port))
                    print(f"✅ 포트 {port} 사용 가능")
                    return port
            except OSError as e:
                print(f"❌ 포트 {port} 사용 불가: {str(e)}")
                continue
        
        print("❌ 사용 가능한 포트를 찾을 수 없음")
        return None
    
    def start_server(self):
        """웹 서버 시작"""
        if self.is_running:
            return
            
        # index.html 파일 확인
        index_file = self.find_index_file()
        if not index_file:
            messagebox.showerror(
                "오류", 
                "index.html 파일을 찾을 수 없습니다.\n현재 디렉토리에 index.html 파일을 생성해주세요."
            )
            return
        
        # 포트 찾기
        self.port = self.find_available_port()
        if not self.port:
            messagebox.showerror("오류", "사용 가능한 포트를 찾을 수 없습니다.")
            return
        
        try:
            print(f"🚀 서버 시작 시도: localhost:{self.port}")
            print(f"📁 작업 디렉토리: {os.getcwd()}")
            print(f"📄 index 파일: {index_file}")
            
            # UI 먼저 업데이트
            self.is_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="🔄 서버 시작 중...", fg="orange")
            
            # 웹 서버 시작 (별도 스레드에서)
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            # 잠시 대기 후 서버 상태 확인
            self.root.after(1000, self._check_server_status)
            
        except Exception as e:
            print(f"❌ 서버 시작 오류: {str(e)}")
            messagebox.showerror("오류", f"서버 시작 중 오류가 발생했습니다:\n{str(e)}")
            self._reset_ui()
    
    def _check_server_status(self):
        """서버 상태 확인 및 UI 업데이트"""
        if self.is_running and self.httpd:
            # 서버가 정상적으로 시작된 경우
            self.status_label.config(text="🟢 서버 실행 중", fg="green")
            self.stop_page_button.config(state="normal")
            
            server_url = f"http://localhost:{self.port}"
            self.url_label.config(text=f"🌐 {server_url}")
            
            # 브라우저에서 열기 (별도 스레드에서)
            self._open_browser_async(server_url)
                
        elif self.is_running:
            # 서버 시작이 실패한 경우
            print("❌ 서버 시작 실패 - 상태 리셋")
            self._reset_ui()
    
    def _open_browser_async(self, url):
        """브라우저를 별도 스레드에서 열기"""
        def open_browser_thread():
            try:
                print(f"🌏 브라우저에서 {url} 열기 시도...")
                webbrowser.open(url)
                print(f"✅ 브라우저 열기 성공")
            except Exception as e:
                print(f"⚠️ 브라우저 열기 실패: {str(e)}")
        
        browser_thread = threading.Thread(target=open_browser_thread, daemon=True)
        browser_thread.start()
    
    def _run_server(self):
        """실제 웹 서버 실행 (별도 스레드)"""
        try:
            # 현재 디렉토리를 명시적으로 설정
            os.chdir(Path.cwd())
            
            # HTTP 핸들러 설정
            handler = http.server.SimpleHTTPRequestHandler
            
            # 커스텀 TCPServer 클래스로 빠른 종료 지원
            class FastShutdownTCPServer(socketserver.TCPServer):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # 소켓 재사용 허용
                    self.allow_reuse_address = True
                    # 빠른 종료를 위한 설정
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    # 연결 대기 시간 단축
                    self.timeout = 1.0
                
                def server_close(self):
                    """서버 종료 시 모든 연결 강제 종료"""
                    try:
                        # 소켓 즉시 종료
                        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 
                                             socket.struct.pack('ii', 1, 0))
                    except:
                        pass
                    super().server_close()
            
            # 서버 생성 및 바인딩
            self.httpd = FastShutdownTCPServer(("localhost", self.port), handler)
            
            print(f"서버가 포트 {self.port}에서 시작되었습니다.")
            print(f"서빙 디렉토리: {os.getcwd()}")
            
            # 서버 시작 성공을 UI에 알림
            self.root.after(0, lambda: print(f"✅ 서버 바인딩 성공: localhost:{self.port}"))
            
            # 서버 실행 (타임아웃으로 반응성 향상)
            while self.is_running:
                self.httpd.handle_request()
            
        except OSError as e:
            error_msg = f"포트 바인딩 오류: {str(e)}\n포트 {self.port}가 이미 사용 중일 수 있습니다."
            print(f"❌ {error_msg}")
            if self.is_running:
                self.root.after(0, lambda: messagebox.showerror("서버 오류", error_msg))
                self.root.after(0, self._reset_ui)
        except Exception as e:
            error_msg = f"서버 실행 중 오류: {str(e)}"
            print(f"❌ {error_msg}")
            if self.is_running:
                self.root.after(0, lambda: messagebox.showerror("서버 오류", error_msg))
                self.root.after(0, self._reset_ui)
    
    def stop_server(self):
        """웹 서버 중지"""
        if not self.is_running:
            return
            
        print("🛑 서버 중지 시작...")
        
        try:
            # 먼저 실행 플래그를 False로 설정
            self.is_running = False
            
            if self.httpd:
                print("📡 모든 연결 강제 종료 중...")
                
                # 1. 소켓 레벨에서 강제 종료
                try:
                    import struct
                    # SO_LINGER 옵션으로 즉시 종료
                    self.httpd.socket.setsockopt(
                        socket.SOL_SOCKET, 
                        socket.SO_LINGER, 
                        struct.pack('ii', 1, 0)  # linger on, timeout 0
                    )
                except Exception as e:
                    print(f"⚠️ 소켓 linger 설정 실패: {e}")
                
                # 2. 서버 셧다운 (논블록킹)
                def force_shutdown():
                    try:
                        self.httpd.shutdown()
                        print("✅ 서버 셧다운 완료")
                    except Exception as e:
                        print(f"⚠️ 셧다운 중 오류: {e}")
                    
                    try:
                        self.httpd.server_close()
                        print("✅ 서버 소켓 닫기 완료")
                    except Exception as e:
                        print(f"⚠️ 소켓 닫기 중 오류: {e}")
                    
                    self.httpd = None
                
                # 강제 종료를 별도 스레드에서 실행 (타임아웃 적용)
                shutdown_thread = threading.Thread(target=force_shutdown, daemon=True)
                shutdown_thread.start()
                
                # 최대 2초 대기
                shutdown_thread.join(timeout=2.0)
                
                if shutdown_thread.is_alive():
                    print("⚠️ 서버 종료가 지연되고 있습니다 (강제 종료됨)")
                    self.httpd = None
            
            self._reset_ui()
            
            # 사용자에게 브라우저 탭 닫기 안내
            messagebox.showinfo(
                "서버 중지", 
                f"✅ 웹 서버가 중지되었습니다.\n"
            )
            
            print("✅ 서버 중지 완료")
            
        except Exception as e:
            print(f"❌ 서버 중지 중 오류: {e}")
            # 오류가 발생해도 UI는 리셋
            self.is_running = False
            self._reset_ui()
            messagebox.showerror("오류", f"서버 중지 중 오류가 발생했습니다:\n{str(e)}\n\n서버는 강제로 중지되었습니다.")
    
    def _create_stop_page(self):
        """서버 중지 알림 페이지 생성 (실험적)"""
        stop_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>서버 중지됨</title>
            <meta charset="utf-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    margin: 0;
                    padding: 50px;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                    padding: 40px;
                    max-width: 500px;
                    margin: 0 auto;
                }
                h1 { font-size: 2.5em; margin-bottom: 20px; }
                p { font-size: 1.2em; line-height: 1.6; }
                .emoji { font-size: 3em; margin: 20px 0; }
            </style>
            <script>
                // 3초 후 탭 닫기 시도
                setTimeout(function() {
                    window.close();
                    // window.close()가 작동하지 않으면 안내 메시지 표시
                    setTimeout(function() {
                        document.getElementById('close-msg').style.display = 'block';
                    }, 1000);
                }, 3000);
            </script>
        </head>
        <body>
            <div class="container">
                <div class="emoji">🛑</div>
                <h1>서버가 중지되었습니다</h1>
                <p>웹 서버가 정상적으로 중지되었습니다.</p>
                <p>이 탭은 3초 후 자동으로 닫힙니다.</p>
                <div id="close-msg" style="display:none;">
                    <p><strong>⚠️ 이 탭을 수동으로 닫아주세요.</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            stop_page_path = Path.cwd() / "_server_stop.html"
            with open(stop_page_path, 'w', encoding='utf-8') as f:
                f.write(stop_html)
            return stop_page_path
        except Exception as e:
            print(f"중지 페이지 생성 실패: {e}")
            return None
    
    def navigate_to_stop_page(self):
        """중지 페이지로 브라우저 이동 (실험적)"""
        if not self.is_running:
            return
            
        try:
            # 임시 중지 페이지 생성
            stop_page_path = self._create_stop_page()
            if stop_page_path:
                stop_url = f"http://localhost:{self.port}/_server_stop.html"
                self._open_browser_async(stop_url)
                messagebox.showinfo(
                    "중지 페이지", 
                    "브라우저가 중지 페이지로 이동합니다.\n"
                    "3초 후 탭이 자동으로 닫힙니다."
                )
        except Exception as e:
            print(f"중지 페이지 이동 실패: {e}")
    
    def _reset_ui(self):
        """UI 상태 리셋"""
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.stop_page_button.config(state="disabled")
        self.status_label.config(text="⏹️ 서버 중지됨", fg="red")
        self.url_label.config(text="")
        self.port = None
        
        # 임시 중지 페이지 파일 제거
        try:
            stop_page_path = Path.cwd() / "_server_stop.html"
            if stop_page_path.exists():
                stop_page_path.unlink()
        except Exception as e:
            print(f"임시 파일 제거 실패: {e}")
    
    def open_browser(self, event=None):
        """브라우저에서 URL 열기 (클릭 이벤트)"""
        if self.is_running and self.port:
            url = f"http://localhost:{self.port}"
            self._open_browser_async(url)
    
    def on_closing(self):
        """프로그램 종료 시 서버 정리"""
        if self.is_running:
            self.stop_server()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

def main():
    """메인 함수"""
    app = WebServerGUI()
    app.run()

if __name__ == "__main__":
    main()
