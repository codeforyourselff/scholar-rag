# Main entry point for the Scholar RAG Web Application
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from uvicorn import run

# manage the lifecycle of external resources (e.g., database connections, background tasks)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic here
    yield
    # Cleanup logic here

# Function to create the FastAPI application
def create_application():
    app = FastAPI(
        title="Scholar RAG Web App",
        description="A web application for the Scholar RAG system.",
        version="1.0.0",
        lifespan=lifespan
    )
    return app

# Create the FastAPI application
app = create_application()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Scholar RAG Web App!"}

# Run the application
if __name__ == "__main__":
    run(app, host="0.0.0.0", port=int(os.getenv("FASTAPI_PORT", 8000)))