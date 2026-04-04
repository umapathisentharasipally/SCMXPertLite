from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
from back_end.routes import auth 
from back_end import run
import os
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(dotenv_path=ROOT_DIR / '.env')

# Create FastAPI app
app = FastAPI( 
    title="SCMXPertLite API",
    description="API for SCMXPertLite, a tool for supply chain management and optimization.",
    version="1.0.0",   
)

# Include routes
app.include_router(auth.router)
#app.include_router(run.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to SCMXPertLite API!",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
def read_health():
    return {
        "status": "healthy",
        "service": "SCMXPertLite API",
        "version": "1.0.0"
    }

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)