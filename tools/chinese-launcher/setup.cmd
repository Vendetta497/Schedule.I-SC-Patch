@echo off
"%~dp0runtime\python.exe" "%~dp0launcher.py" --setup
if errorlevel 1 pause
