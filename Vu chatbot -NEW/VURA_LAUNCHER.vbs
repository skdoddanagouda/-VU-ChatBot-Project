Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c python backend/server.py", 1, False
WScript.Sleep 2000
WshShell.Run "http://127.0.0.1:5050"
