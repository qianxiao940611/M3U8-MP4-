@echo off
chcp 65001 >nul
echo ========================================
echo 视频批量下载工具 - 一键打包为EXE
echo ========================================
echo.
echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误：未找到Python环境！
    echo 请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo.
echo 开始打包程序...
python build_exe.py

echo.
echo 打包完成！
echo 可执行文件位置：dist\视频批量下载工具.exe
echo.
pause