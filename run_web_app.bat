@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

set HOST=127.0.0.1
set PORT=5000

REM Install dependencies
echo Verificando dependencias...
pip install -q flask gunicorn qiskit qiskit-aer 2>nul

echo.
echo ============================================
echo Iniciando la aplicacion Flask con Qiskit
echo http://%HOST%:%PORT%/
echo ============================================
echo.
echo Deja esta ventana abierta mientras usas la app.
echo Para detenerla, presiona CTRL+C.
echo.

timeout /t 2 /nobreak
start "" "http://%HOST%:%PORT%/"

REM Run Flask app
.venv\Scripts\python.exe app.py
