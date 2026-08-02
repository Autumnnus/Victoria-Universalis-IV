@echo off
rem Victoria Universalis IV - localization pipeline.
rem Run `loc` for the menu, or `loc status`, `loc sync turkish`, `loc verify`, ...
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python -m tools.loc %*
endlocal
