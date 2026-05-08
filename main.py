from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import logging
import uvicorn
from back_end.routes.auth import user_auth_routes, admin_auth_routes
from back_end.routes import (
    device_route,
    shipment_route
)

from back_end.config import ROOT_DIR


# ==================== LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="SCMXPertLite API",
    description="Supply Chain Management & IoT Tracking Platform",
    version="1.0.0"
)


# ==================== CORS ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ROUTERS ====================

app.include_router(user_auth_routes.router)
app.include_router(admin_auth_routes.router)
app.include_router(device_route.router)
app.include_router(shipment_route.router)


# ==================== ROOT ====================

@app.get("/")
async def read_root():
    return {
        "message": "Welcome to SCMXPertLite API",
        "docs": "/docs",
        "health": "/api/health",
        "version": "1.0.0"
    }


# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def read_health():
    return {
        "status": "healthy",
        "service": "SCMXPertLite API",
        "version": "1.0.0"
    }


# ==================== GLOBAL ERROR HANDLER ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
            "error": str(exc)
        }
    )


# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    logger.info("SCMXPertLite API started successfully")


# ==================== SHUTDOWN EVENT ====================

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("SCMXPertLite API shutdown")


# ==================== MAIN ====================

if __name__ == "__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)