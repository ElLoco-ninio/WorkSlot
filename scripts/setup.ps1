Write-Host "Setting up WorkSlot V1..."

Write-Host "Installing Backend Dependencies..."
cd backend
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
python -m alembic upgrade head
cd ..

Write-Host "Installing Frontend Dependencies..."
cd frontend
npm install
cd ..

Write-Host "Setup Complete!"
