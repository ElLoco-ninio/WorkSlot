from sqlmodel import SQLModel, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/workslot")

engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)
