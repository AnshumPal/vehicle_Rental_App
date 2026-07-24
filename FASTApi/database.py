from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/rental_db"

engine = create_engine(DATABASE_URL,
            "postgresql://postgres:postgres123@localhost:5432/rental_db"
)



engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db =  sessionLocal()
    try:
        yield db
    finally:
        db.close()