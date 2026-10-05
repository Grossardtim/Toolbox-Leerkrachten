"""Start the local portal and open the browser only after the server is ready."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent.parent


def port_in_use(port):
    with socket.socket() as connection:
        connection.settimeout(0.4)
        return connection.connect_ex(('127.0.0.1', port)) == 0


def portal_ready(url):
    try:
        with urllib.request.urlopen(url + 'aanmelden/', timeout=1) as response:
            page = response.read(128000).decode('utf-8', errors='replace')
            return response.status == 200 and ('LEERKRACHTEN TOOL' in page or 'LEERKRACHTENPORTAAL' in page) and 'Atheneum Tungrorum' in page
    except (OSError, urllib.error.URLError):
        return False


def open_site(url, enabled):
    if enabled and not webbrowser.open(url):
        print(f'Open zelf deze link in je browser: {url}', flush=True)


def main():
    parser = argparse.ArgumentParser(description='Start het lokale leerkrachtenportaal.')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('De poort moet tussen 1 en 65535 liggen.')
    os.chdir(ROOT)
    url = f'http://127.0.0.1:{args.port}/'
    if port_in_use(args.port):
        if portal_ready(url):
            print(f'De tool draait al: {url}', flush=True)
            open_site(url, not args.no_browser)
            return 0
        print(f'Poort {args.port} is bezet door een ander programma. Er is niets afgesloten.', flush=True)
        return 1
    print(f'Server starten op {url}\nHoud dit venster open. Stoppen: Ctrl+C.', flush=True)
    server = subprocess.Popen([sys.executable, 'desktop.py', '--data-dir', str(ROOT/'data'),
                               '--port', str(args.port), '--no-browser'], cwd=ROOT)
    try:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if server.poll() is not None:
                return server.returncode or 1
            if portal_ready(url):
                print(f'Klaar: {url}', flush=True)
                open_site(url, not args.no_browser)
                return server.wait()
            time.sleep(0.3)
        print('De server werd niet tijdig gereed. Controleer de foutmelding hierboven.', flush=True)
        return 1
    except KeyboardInterrupt:
        print('\nServer gestopt.', flush=True)
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == '__main__':
    sys.exit(main())
