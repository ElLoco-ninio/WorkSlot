$env:PYTHONPATH = "backend"
cd backend
python -m alembic upgrade head
cd ..
