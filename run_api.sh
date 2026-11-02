#!/usr/bin/env bash
# Study Buddy API - Development Server
# Use --reload-dir to only watch API code, exclude data/ to prevent restarts on uploads
uvicorn api.main:app --reload --reload-dir api --port 8000
