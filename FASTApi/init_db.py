from database import Base, engine
from FASTApi.models import Booking 

def init():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

init()
