from sqlalchemy import Column, Integer, String
from database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id      = Column(Integer, primary_key=True, index=True)
    user    = Column(String, nullable=False)
    vehicle = Column(String, nullable=False)
    status  = Column(String, default="confirmed")