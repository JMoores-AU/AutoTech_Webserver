@echo off
if "%CTRL_MODE%"=="%SIMULATION_MODE%" (
    COLOR 07
) else (
    if "%CTRL_MODE%"=="%LISTEN_MODE%" (
        COLOR 3f
    ) else (
        if "%CTRL_MODE%"=="%PRODUCTION_MODE%" (
            COLOR 4f
        ) else (
            COLOR 7D
        )
    )
)
