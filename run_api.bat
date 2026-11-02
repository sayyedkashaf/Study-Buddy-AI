@echo off
REM Study Buddy API - Development Server
REM Use --reload-dir to only watch API code, exclude data/ to prevent restarts on uploads
uvicorn api.main:app --reload --reload-dir api --port 8000
