@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "MAIL_BRIDGE_NODE=node.exe"
where node.exe >nul 2>nul
if not errorlevel 1 goto run
set "MAIL_BRIDGE_NODE=%LOCALAPPDATA%\OpenAI\Codex\bin\node.exe"
if exist "%MAIL_BRIDGE_NODE%" goto run
echo Node.js was not found. Open the Codex desktop app once or use the manual commands in INSTALL.md.
set "MAIL_BRIDGE_EXIT=1"
goto finish
:run
"%MAIL_BRIDGE_NODE%" "%~dp0scripts\install-local.cjs" %*
set "MAIL_BRIDGE_EXIT=%ERRORLEVEL%"
:finish
if "%~1"=="" pause
exit /b %MAIL_BRIDGE_EXIT%
