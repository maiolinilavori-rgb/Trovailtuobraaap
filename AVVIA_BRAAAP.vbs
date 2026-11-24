Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run """_internal\pythonw.exe"" ""_internal\avvia.py""", 0, False
WScript.Sleep 1500
WshShell.Run "http://127.0.0.1:5000", 1, False
