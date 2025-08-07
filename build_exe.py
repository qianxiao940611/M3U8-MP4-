#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载工具打包脚本
使用PyInstaller将Python程序打包为exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装成功！")
        return True
    except subprocess.CalledProcessError:
        print("PyInstaller安装失败！")
        return False

def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''
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
'''
    
    with open('video_downloader.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("已创建spec文件: video_downloader.spec")

def build_exe():
    """构建exe文件"""
    print("开始构建exe文件...")
    try:
        # 使用spec文件构建
        subprocess.check_call(["pyinstaller", "--clean", "video_downloader.spec"])
        print("构建完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def copy_additional_files():
    """复制额外的文件到dist目录"""
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("dist目录不存在")
        return
    
    # 要复制的文件列表
    files_to_copy = [
        "README.md",
        "requirements.txt",
        "test_links.txt"
    ]
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            try:
                shutil.copy2(file_name, dist_dir)
                print(f"已复制: {file_name}")
            except Exception as e:
                print(f"复制{file_name}失败: {e}")
    
    # 创建downloads目录
    downloads_dir = dist_dir / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    print("已创建downloads目录")

def main():
    """主函数"""
    print("=" * 50)
    print("视频批量下载工具 - 打包脚本")
    print("=" * 50)
    
    # 检查必要文件
    required_files = ['video_downloader.py', 'ffmpeg.exe', 'ffplay.exe', 'aria2c.exe']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"缺少必要文件: {', '.join(missing_files)}")
        print("请确保所有必要文件都在当前目录中")
        return False
    
    # 安装PyInstaller
    if not install_pyinstaller():
        return False
    
    # 创建spec文件
    create_spec_file()
    
    # 构建exe
    if not build_exe():
        return False
    
    # 复制额外文件
    copy_additional_files()
    
    print("\n" + "=" * 50)
    print("打包完成！")
    print("可执行文件位置: dist/视频批量下载工具.exe")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            input("\n按回车键退出...")
        else:
            input("\n打包失败，按回车键退出...")
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"\n发生错误: {e}")
        input("按回车键退出...")