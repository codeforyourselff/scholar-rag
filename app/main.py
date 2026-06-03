# Main entry point for the Scholar RAG Web Application
import os
from fastapi import FastAPI
from uvicorn import run

# Function to create the FastAPI application
def create_application():
    app = FastAPI()
    return app

# Create the FastAPI application
app = create_application()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Scholar RAG Web App!"}

# Run the application
if __name__ == "__main__":
    run(app, host="0.0.0.0", port=int(os.getenv("FASTAPI_PORT", 8000)))
