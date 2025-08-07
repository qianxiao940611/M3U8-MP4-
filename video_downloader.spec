
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['video_downloader.py'],
    pathex=[],
    binaries=[
        ('ffmpeg.exe', '.'),
        ('ffplay.exe', '.'),
        ('aria2c.exe', '.'),
    ],
    datas=[
        ('test_links.txt', '.'),
        ('icon.svg', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinterdnd2',
        'requests',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'threading',
        'subprocess',
        'concurrent.futures',
        're',
        'os',
        'sys',
        'time',
        'urllib.parse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='视频批量下载工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico' if os.path.exists('icon.ico') else None,
)
