# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts/widget_grafo.py'],
    pathex=[],
    binaries=[],
    datas=[('www/cerebro.html', 'www'), ('scripts/generate-graph-html.py', 'scripts'), ('conhecimento/notas', 'conhecimento/notas')],
    hiddenimports=['numpy', 'psutil', 'webview', 'importlib.util'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CerebroVivo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
