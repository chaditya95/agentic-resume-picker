#!/usr/bin/env bash
set -e
pyinstaller --onefile resume_selector/src/main.py --name resume_selector
