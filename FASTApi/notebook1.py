import time
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Booking, Base

# create tables if not exists
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vehicle Rental API",
    description="A production grade rental API",
    version="1.0.0"
)

# ── OBSERVER PATTERN ──────────────────────────
class Observer(ABC):
    @abstractmethod
    def notify(self, user: str, vehicle: str) -> None:
        pass

class SMSNotification(Observer):
    def notify(self, user: str, vehicle: str) -> None:
        print(f"SMS → {user}: your {vehicle} is booked ✓")

class EmailNotification(Observer):
    def notify(self, user: str, vehicle: str) -> None:
        print(f"Email → {user}: booking confirmation for {vehicle} ✓")

# ── SINGLETON PATTERN ─────────────────────────
class RentalDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("opening database connection...")
            cls._instance = super().__new__(cls)
            cls._instance._observers = []
        return cls._instance

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def notify_all(self, user: str, vehicle: str) -> None:
        for observer in self._observers:
            observer.notify(user, vehicle)

# ── FACTORY PATTERN ───────────────────────────
class Vehical(ABC):
    @abstractmethod
    def get_info(self) -> str:
        pass

class Car(Vehical):
    def get_info(self) -> str:
        return "4 wheels, seats 5, fuel: petrol"

class Bike(Vehical):
    def get_info(self) -> str:
        return "2 wheels, seats 2, fuel: petrol"

class Truck(Vehical):
    def get_info(self) -> str:
        return "6 wheels, seats 2, fuel: diesel"

class ElectricCar(Vehical):
    def get_info(self) -> str:
        return "4 wheels, seats 5, fuel: electric"

class Scooter(Vehical):
    def get_info(self) -> str:
        return "2 wheels, seats 1, fuel: electric"

class VehicleFactory:
    _vehicles = {
        "car":         Car,
        "bike":        Bike,
        "truck":       Truck,
        "electriccar": ElectricCar,
        "scooter":     Scooter,
    }

    @staticmethod
    def create(vehicle_type: str) -> Vehical:
        vehicle_class = VehicleFactory._vehicles.get(vehicle_type)
        if not vehicle_class:
            return None
        return vehicle_class()

    @staticmethod
    def available_types() -> list:
        return list(VehicleFactory._vehicles.keys())

# ── SETUP ─────────────────────────────────────
db_singleton = RentalDatabase()
db_singleton.subscribe(SMSNotification())
db_singleton.subscribe(EmailNotification())

# ── MODELS ────────────────────────────────────
class BookingRequest(BaseModel):
    user: str
    vehicle_type: str

class CancelRequest(BaseModel):
    booking_id: int

# ── MIDDLEWARE ────────────────────────────────
@app.middleware("http")
async def log_request(request: Request, call_next):
    start = time.time()
    print(f"-> {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"<- {response.status_code} {time.time() - start:.3f}s")
    return response

API_KEY = "rental-secret-key-2026"

@app.middleware("http")
async def authenticate(request: Request, call_next):
    if request.url.path in ["/", "/docs", "/openapi.json", "/status"]:
        return await call_next(request)
    api_key = request.headers.get("X-API-KEY")
    if api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized"}
        )
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── ENDPOINTS ─────────────────────────────────
@app.get("/")
def home():
    return {"message": "Welcome to Vehicle Rental API"}

@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    total = db.query(Booking).count()
    return {
        "status": "running",
        "total_bookings": total,
        "database": "postgresql://localhost/rental_db"
    }

@app.get("/vehicles")
def get_vehicles():
    vehicles = []
    for v_type in VehicleFactory.available_types():
        vehicle = VehicleFactory.create(v_type)
        vehicles.append({
            "type": v_type,
            "info": vehicle.get_info()
        })
    return {"vehicles": vehicles}

@app.get("/vehicles/count")
def vehicle_count():
    return {
        "total": len(VehicleFactory.available_types()),
        "types": VehicleFactory.available_types()
    }

@app.get("/vehicles/{vehicle_type}")
def get_vehicle_info(vehicle_type: str):
    vehicle = VehicleFactory.create(vehicle_type)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"vehicle '{vehicle_type}' not found"
        )
    return {"type": vehicle_type, "info": vehicle.get_info()}

@app.post("/book", status_code=status.HTTP_201_CREATED)
def book_vehicle(booking: BookingRequest, db: Session = Depends(get_db)):
    vehicle = VehicleFactory.create(booking.vehicle_type)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"vehicle '{booking.vehicle_type}' not found"
        )
    new_booking = Booking(
        user=booking.user,
        vehicle=booking.vehicle_type,
        status="confirmed"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    db_singleton.notify_all(booking.user, booking.vehicle_type)
    return {
        "message": "booking confirmed",
        "booking": {
            "id": new_booking.id,
            "user": new_booking.user,
            "vehicle": new_booking.vehicle,
            "status": new_booking.status
        },
        "vehicle_info": vehicle.get_info()
    }

@app.get("/bookings")
def get_bookings(db: Session = Depends(get_db)):
    all_bookings = db.query(Booking).all()
    if not all_bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no bookings yet"
        )
    return {
        "total": len(all_bookings),
        "bookings": [
            {
                "id": b.id,
                "user": b.user,
                "vehicle": b.vehicle,
                "status": b.status
            } for b in all_bookings
        ]
    }

@app.get("/bookings/{user}")
def get_user_bookings(user: str, db: Session = Depends(get_db)):
    user_bookings = db.query(Booking).filter(Booking.user == user).all()
    if not user_bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no bookings found for {user}"
        )
    return {
        "user": user,
        "bookings": [
            {
                "id": b.id,
                "user": b.user,
                "vehicle": b.vehicle,
                "status": b.status
            } for b in user_bookings
        ]
    }

@app.post("/cancel")
def cancel_booking(request: CancelRequest, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(
        Booking.id == request.booking_id
    ).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"booking {request.booking_id} not found"
        )
    db.delete(booking)
    db.commit()
    return {"message": f"booking {request.booking_id} cancelled successfully"}

