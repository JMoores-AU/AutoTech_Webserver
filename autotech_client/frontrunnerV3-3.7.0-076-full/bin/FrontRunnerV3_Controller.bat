@echo off

@setlocal

@set FRV3_BINDIR=%~dp0
@set Path=%FRV3_BINDIR%;%Path%
@rem echo FRV3_BINDIR=%FRV3_BINDIR%
@rem pause

@if /I "X%FRV3_DOMAIN%"=="X" goto :CONFIG_ERROR

@set MMSDOMAIN=%FRV3_DOMAIN%

call frontrunner start controller
@goto :END_EXEC

:CONFIG_ERROR
@echo Environment parameters are not correctly configured.
@echo Execute bin\FRClientInstaller.wsf in the install directory of FrontRunner Controller.
@pause

:END_EXEC

@endlocal
