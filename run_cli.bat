@echo off
setlocal
set "CONDA_PYTHON=%USERPROFILE%\miniconda3\envs\osdagbridge-env\python.exe"

if exist "%CONDA_PYTHON%" (
    set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
    "%CONDA_PYTHON%" -m osdagbridge.cli.__main__ %*
) else (
    call conda activate osdagbridge-env && python -m osdagbridge.cli.__main__ %*
)
endlocal
