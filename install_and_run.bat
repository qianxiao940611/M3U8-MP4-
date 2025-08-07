@echo off
chcp 65001
echo ========================================
echo M3U8/MP4 批量下载工具 v2.0
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python环境，请先安装Python 3.7+
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

echo 正在安装依赖库...
pip install -r requirements.txt

if errorlevel 1 (
    echo 警告：部分依赖库安装失败，程序可能无法正常运行
    echo 请手动执行：pip install -r requirements.txt
    echo.
)

echo.
echo 正在检查FFmpeg工具...
if not exist "ffmpeg.exe" (
    echo 警告：未找到ffmpeg.exe，M3U8下载功能可能无法使用
    echo 请将ffmpeg.exe、ffplay.exe、ffprobe.exe放置在程序目录下
    echo.
)

if not exist "ffplay.exe" (
    echo 警告：未找到ffplay.exe，视频播放功能可能无法使用
    echo.
)

echo 启动程序...
echo.
python video_downloader.py

if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查错误信息
    pause
)

echo.
echo 程序已退出
pause