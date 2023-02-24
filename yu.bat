@ECHO OFF

@REM 直接使用特定的Python解释器来运行，适用于安装了多版本Python或virtualenv时。
@SET PYTHON_PATH=""

@REM 使用conda环境运行时，conda环境的名称。
@SET CONDA_ENV="yudo"

@REM 如果 yu start 无法启动conda环境，请尝试修改以下配置。
@SET CONDA_PATH="C:\ProgramData\Miniconda3\condabin\"

TITLE yudo
IF "%1"=="start" (
    %CONDA_PATH%conda activate %CONDA_ENV%
) ELSE IF "%1"=="#install" (
    %PYTHON_PATH%python -m pip install -r "%~dp0\requirements.txt"
) ELSE (
    CMD /C "%PYTHON_PATH%python %~dp0\main.py %*"
)
