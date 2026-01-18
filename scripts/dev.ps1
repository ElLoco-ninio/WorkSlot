$root = Get-Location
$backend = Start-Process -FilePath "$root\backend\venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --port 8000" -WorkingDirectory "$root\backend" -PassThru -NoNewWindow
$frontend = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "$root\frontend" -PassThru -NoNewWindow

Write-Host "Servers started. Press Enter to stop..."
Read-Host

Stop-Process -Id $backend.Id
Stop-Process -Id $frontend.Id
