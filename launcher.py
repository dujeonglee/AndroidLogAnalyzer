#!/usr/bin/env python3
import os
import sys
import http.server
import socketserver
import webbrowser
from pathlib import Path

def find_index_file():
    """현재 디렉토리에서 index HTML 파일을 찾습니다."""
    current_dir = Path.cwd()
    
    # 일반적인 index 파일명들
    index_patterns = [
        'index.html',
        'index.htm',
        'Index.html',
        'INDEX.html',
        'home.html',
        'main.html'
    ]
    
    for pattern in index_patterns:
        index_file = current_dir / pattern
        if index_file.exists():
            return index_file
    
    return None

def find_available_port(start_port=8000):
    """사용 가능한 포트를 찾습니다."""
    import socket
    
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    
    return None

def start_web_server():
    """웹 서버를 시작합니다."""
    # index 파일 찾기
    index_file = find_index_file()
    
    if not index_file:
        print("❌ index HTML 파일을 찾을 수 없습니다.")
        print("현재 디렉토리:", os.getcwd())
        print("찾는 파일명: index.html, index.htm, Index.html, INDEX.html, home.html, main.html")
        return False
    
    print(f"✅ 발견된 index 파일: {index_file.name}")
    print(f"📁 현재 디렉토리: {os.getcwd()}")
    
    # 사용 가능한 포트 찾기
    port = find_available_port()
    if not port:
        print("❌ 사용 가능한 포트를 찾을 수 없습니다.")
        return False
    
    # 웹 서버 시작
    try:
        handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", port), handler)
        
        server_url = f"http://localhost:{port}"
        print(f"\n🚀 웹 서버가 시작되었습니다!")
        print(f"🌐 URL: {server_url}")
        print(f"📄 Index 파일: {index_file.name}")
        print(f"🛑 서버를 중지하려면 Ctrl+C를 눌러주세요.\n")
        
        # 브라우저에서 자동으로 열기 (선택사항)
        try:
            webbrowser.open(server_url)
            print("🌏 기본 브라우저에서 페이지를 열었습니다.")
        except:
            print("⚠️  브라우저를 자동으로 열 수 없습니다. 수동으로 위 URL을 방문해주세요.")
        
        print("-" * 50)
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 서버가 중지되었습니다.")
        httpd.shutdown()
        return True
    except Exception as e:
        print(f"❌ 서버 시작 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 50)
    print("🌐 HTML 웹 서버 시작 도구")
    print("=" * 50)
    
    # 현재 디렉토리의 HTML 파일들 표시
    html_files = list(Path.cwd().glob("*.html")) + list(Path.cwd().glob("*.htm"))
    if html_files:
        print(f"\n📋 현재 디렉토리의 HTML 파일들:")
        for html_file in html_files:
            print(f"   - {html_file.name}")
    
    print()
    start_web_server()

if __name__ == "__main__":
    main()