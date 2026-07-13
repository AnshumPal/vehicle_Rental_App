from fastapi import FastAPI
from pydantic import BaseModel
from abc import ABC, abstractmethod

app = FastAPI()

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
            cls._instance.bookings = []
            cls._instance.total_bookings = 0
            cls._instance._observers = []
        return cls._instance

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def save_booking(self, user: str, vehicle: str) -> dict:
        self.total_bookings += 1
        booking = {
            "id": self.total_bookings,
            "user": user,
            "vehicle": vehicle,
            "status": "confirmed"
        }
        self.bookings.append(booking)
        for observer in self._observers:
            observer.notify(user, vehicle)
        return booking

    def get_all_bookings(self) -> list:
        return self.bookings

    def get_user_bookings(self, user: str) -> list:
        return [b for b in self.bookings if b["user"] == user]

    def cancel_booking(self, booking_id: int) -> bool:
        for booking in self.bookings:
            if booking["id"] == booking_id:
                self.bookings.remove(booking)
                return True
        return False

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
db = RentalDatabase()
db.subscribe(SMSNotification())
db.subscribe(EmailNotification())

# ── MODELS ────────────────────────────────────
class BookingRequest(BaseModel):
    user: str
    vehicle_type: str

class CancelRequest(BaseModel):
    booking_id: int

# ── ENDPOINTS ─────────────────────────────────
@app.get("/")
def home():
    return {"message": "Welcome to Vehicle Rental API"}

@app.get("/status")
def status():
    return {
        "status": "running",
        "total_bookings": db.total_bookings,
        "database": "rental.database.com"
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
        return {"error": f"vehicle '{vehicle_type}' not found"}
    return {"type": vehicle_type, "info": vehicle.get_info()}

@app.post("/book")
def book_vehicle(booking: BookingRequest):
    vehicle = VehicleFactory.create(booking.vehicle_type)
    if not vehicle:
        return {"error": f"vehicle '{booking.vehicle_type}' not found"}
    new_booking = db.save_booking(booking.user, booking.vehicle_type)
    return {
        "message": "booking confirmed",
        "booking": new_booking,
        "vehicle_info": vehicle.get_info()
    }

@app.get("/bookings")
def get_bookings():
    all_bookings = db.get_all_bookings()
    if not all_bookings:
        return {"message": "no bookings yet"}
    return {"total": len(all_bookings), "bookings": all_bookings}

@app.get("/bookings/{user}")
def get_user_bookings(user: str):
    user_bookings = db.get_user_bookings(user)
    if not user_bookings:
        return {"message": f"no bookings found for {user}"}
    return {"user": user, "bookings": user_bookings}

@app.post("/cancel")
def cancel_booking(request: CancelRequest):
    success = db.cancel_booking(request.booking_id)
    if success:
        return {"message": f"booking {request.booking_id} cancelled"}
    return {"error": f"booking {request.booking_id} not found"}