"""Integration check using only a temporary copy of the fictitious QA database."""
import http.cookiejar
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='shutdown-',dir=ROOT/'outputs') as tmp:
    tmp=Path(tmp)
    for name in ['schoolportal.sqlite3','.secret']:
        shutil.copy2(ROOT/'outputs/ui-group-qa'/name,tmp/name)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    log=open(tmp/'server.log','w',encoding='utf-8')
    process=subprocess.Popen([sys.executable,str(ROOT/'desktop.py'),'--data-dir',str(tmp),'--port',str(port),'--no-browser'],cwd=ROOT,stdout=log,stderr=log)
    try:
        url=f'http://127.0.0.1:{port}'
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        for _ in range(100):
            try:
                page=opener.open(url+'/aanmelden/',timeout=1).read().decode();break
            except OSError:time.sleep(.1)
        else:raise AssertionError('Server did not start')
        def token(page):return re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',page).group(1)
        data=urllib.parse.urlencode({'username':'demo.leerkracht','password':'iPGpWhZpIYS32TDYIdcI_Q','csrfmiddlewaretoken':token(page)}).encode()
        page=opener.open(url+'/aanmelden/',data,timeout=5).read().decode()
        assert 'Tool afsluiten' in page
        page=opener.open(url+'/afsluiten/',timeout=5).read().decode()
        data=urllib.parse.urlencode({'csrfmiddlewaretoken':token(page)}).encode()
        response=opener.open(url+'/afsluiten/',data,timeout=5).read().decode()
        assert 'server wordt afgesloten' in response
        assert process.wait(timeout=12)==0
        print('PASS: lokale start, aanmelden, bevestiging, server afsluiten en proces beëindigen; tijdelijke databank.')
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=5)
        log.close()
