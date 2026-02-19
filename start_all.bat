g:\phpstudy_pro\.jqgh\NewInformationTechnology\Agent\start_all.bat
@echo off
chcp 65001 >nul
title 一键启动所有服务

echo ============================================================
echo 🚀 一键启动所有服务
echo ============================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，请先安装Python
    pause
    exit /b 1
)

echo ✅ 检测到Python
echo.

REM 检查依赖包
echo 📦 检查依赖包...
python -c "import flask, tornado, paramiko, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 缺少依赖包，正在安装...
    pip install flask tornado paramiko requests
    if %errorlevel% neq 0 (
        echo ❌ 依赖包安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖包安装完成
) else (
    echo ✅ 依赖包检查完成
)

echo.
echo ============================================================
echo 🚀 正在启动所有服务...
echo ============================================================
echo.

REM 启动Python脚本
python start_all.py

REM 如果脚本退出，暂停以便查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo ❌ 服务启动失败
    pause
)