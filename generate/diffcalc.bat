@echo off
setlocal EnableDelayedExpansion
set CTESTEXE=bin\ctest.exe

if not exist !CTESTEXE! (
    echo.FATAL[diffcalc]: executable does not exist: !CTESTEXE!
    exit /b 1
)

echo.Diffing calculations.

!CTESTEXE! diff 0.0 temp\c_check.txt dotnet\csharp_test\csharp_check.txt
if errorlevel 1 (exit /b 1)

!CTESTEXE! diff 2.7e-14 temp\c_check.txt temp\js_check.txt
if errorlevel 1 (exit /b 1)

!CTESTEXE! diff 1.6e-16 temp\c_check.txt temp\py_check.txt
if errorlevel 1 (exit /b 1)

!CTESTEXE! diff 2.7e-14 temp\js_check.txt temp\py_check.txt
if errorlevel 1 (exit /b 1)

echo.diffcalc: PASS
echo.
exit /b 0
