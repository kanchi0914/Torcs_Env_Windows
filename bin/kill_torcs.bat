@echo off

cd C:\Program Files (x86)\torcs
TASKLIST | FIND "wtorcs.exe" > NUL
IF NOT ERRORLEVEL 1  (
	ECHO wtorcsが起動しています．
	taskkill /im wtorcs.exe /f
) ELSE (
    ECHO wtorcsが起動していません．
)

