# Build on the target operating system. Never include data/ or Codex dependencies.
from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'schoolportal.settings'
os.environ['DATA_DIR'] = str(root / 'build' / 'config')
hidden = []
for package in ('accounts', 'evaluations', 'exports', 'schoolportal', 'waitress', 'xlsxwriter', 'webview'):
    hidden += collect_submodules(package, filter=lambda name: '.test' not in name)
data = [(str(root / 'templates'), 'templates'), (str(root / 'static'), 'static')]
data += collect_data_files('django')
data += collect_data_files('webview')
for package in ('Django', 'waitress', 'XlsxWriter', 'pywebview', 'pythonnet'):
    data += copy_metadata(package)
a = Analysis([str(root / 'desktop.py')], pathex=[str(root)], binaries=[], datas=data,
             hiddenimports=hidden, hookspath=[], runtime_hooks=[],
             excludes=['psycopg', 'psycopg_binary', 'tkinter', 'pytest'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='LeerkrachtenTool',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
