@echo off
setlocal
set "CONDA_PYTHON=%USERPROFILE%\miniconda3\envs\osdagbridge-env\python.exe"

if exist "%CONDA_PYTHON%" (
    echo [OsdagBridge] Launching via osdagbridge-env interpreter...
    set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
    "%CONDA_PYTHON%" -m osdagbridge.desktop.__main__ %*
) else (
    echo [OsdagBridge] osdagbridge-env not found at %CONDA_PYTHON%. Trying conda activate...
    call conda activate osdagbridge-env && python -m osdagbridge.desktop.__main__ %*
)
endlocal
