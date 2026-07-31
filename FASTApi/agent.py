import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

@tool
def get_available_vehicles() -> str:
    """Get list of all available vehicles with prices"""
    return """
    car: 4 wheels, 5 seats, petrol, 800 per day
    bike: 2 wheels, 2 seats, petrol, 300 per day
    truck: 6 wheels, 2 seats, diesel, 1500 per day
    electriccar: 4 wheels, 5 seats, electric, 900 per day
    scooter: 2 wheels, 1 seat, electric, 200 per day
    """

@tool
def book_vehicle(vehicle_type: str, user_name: str) -> str:
    """Book a vehicle for 1 day.
    vehicle_type: car, bike, truck, electriccar, or scooter
    user_name: name of person booking"""
    prices = {
        "car": 800, "bike": 300, "truck": 1500,
        "electriccar": 900, "scooter": 200
    }
    if vehicle_type not in prices:
        return f"Error: {vehicle_type} not available. Choose from: car bike truck electriccar scooter"
    return f"Booking confirmed. {user_name} booked {vehicle_type} for 1 day. Total: Rs {prices[vehicle_type]}"

@tool
def book_vehicle_multiple_days(vehicle_type: str, user_name: str, number_of_days: str) -> str:
    """Book a vehicle for multiple days.
    vehicle_type: car, bike, truck, electriccar, or scooter
    user_name: name of person booking
    number_of_days: number of days as text example 3"""
    try:
        days = int(number_of_days)
    except:
        return "Error: please provide valid number of days"
    if days <= 0:
        return "Error: days must be positive"
    prices = {
        "car": 800, "bike": 300, "truck": 1500,
        "electriccar": 900, "scooter": 200
    }
    if vehicle_type not in prices:
        return f"Error: {vehicle_type} not available"
    total = prices[vehicle_type] * days
    return f"Booking confirmed. {user_name} booked {vehicle_type} for {days} days. Total: Rs {total}"

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile"
)

tools = [get_available_vehicles, book_vehicle, book_vehicle_multiple_days]

system_prompt = """You are a vehicle rental assistant.
Rules:
1. Check available vehicles first using get_available_vehicles
2. Use book_vehicle for 1 day bookings
3. Use book_vehicle_multiple_days for multiple days
4. Never call tool inside another tool
5. One tool at a time
6. Cheapest is scooter Rs 200/day
7. Heavy loads use truck
8. Eco friendly use electriccar
9. If name missing use Guest
"""

agent = create_react_agent(llm, tools, prompt=system_prompt)

def run_agent(user_message: str) -> str:
    result = agent.invoke({
        "messages": [{"role": "user", "content": user_message}]
    })
    return result["messages"][-1].content

if __name__ == "__main__":
    tests = [
        "Book the cheapest vehicle for Anshum for 3 days",
        "Book a helicopter for Anshum for 3 days",
        "Book a car for Ram for -2 days",
        "I need to move furniture. Book for Ram for 2 days",
        "Book an eco friendly vehicle for Raj for 5 days",
    ]

    for test in tests:
        print(f"\nUser: {test}")
        print(f"Agent: {run_agent(test)}")
        print("-" * 50)