Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = baseDir
Set env = WshShell.Environment("PROCESS")
env("BRAAAP_DATA_DIR") = baseDir & "\dati"
env("PYTHONPATH") = baseDir & "\_internal"
WshShell.Run "pyw -3.14 """ & baseDir & "\_internal\app.py""", 0, False
WScript.Sleep 1800
WshShell.Run "http://127.0.0.1:5000", 1, False
