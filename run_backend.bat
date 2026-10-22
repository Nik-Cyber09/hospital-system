@echo off
title Carepoint Hospital Backend (FastAPI)
cd /d "%~dp0"
echo Starting Carepoint Hospital FastAPI backend on port 4000...
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir server --host 0.0.0.0 --port 4000 --reload
pause
