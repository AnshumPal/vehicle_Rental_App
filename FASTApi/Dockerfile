# Layer 1 — base Python image
FROM python:3.11

# Layer 2 — set working directory
WORKDIR /app

# Layer 3 — copy requirements first
COPY requirements.txt .

# Layer 4 — install dependencies
RUN pip install -r requirements.txt

# Layer 5 — copy your code
COPY . .

# Layer 6 — run the app
CMD ["uvicorn", "notebook1:app", "--host", "0.0.0.0", "--port", "8000"]