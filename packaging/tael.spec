# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None
project_root = Path.cwd().resolve()

datas = [
    (str(project_root / 'assets' / 'tael-logo-v3.svg'), 'assets'),
    (str(project_root / 'src' / 'tael' / 'config' / 'defaults.yaml'), 'tael/config'),
]

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespans',
    'uvicorn.lifespans.auto',
    'fastapi',
    'pydantic',
    'yaml',
    'psutil',
    'rich',
    'httpx',
    'sqlite3',
]

a = Analysis(
    [str(project_root / 'src' / 'tael' / 'cli' / '__main__.py')],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='tael',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
