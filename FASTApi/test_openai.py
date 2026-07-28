import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "I need to move furniture this weekend. Which vehicle should I rent from car bike truck electriccar scooter?"
        }
    ]
)

print(response.choices[0].message.content)