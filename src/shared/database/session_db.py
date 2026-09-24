from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("No se encontró DATABASE_URL en el archivo .env")

engine = create_engine(database_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
