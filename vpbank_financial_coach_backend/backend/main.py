from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers which we will create shortly
from .api.routers import auth, chat, jars, transactions, fees, plans, user_settings
from .db.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="VPBank AI Financial Coach API",
    description="Backend service for the multi-agent financial assistant.",
    version="1.0.0"
)

# --- Middleware ---
# Setup CORS (Cross-Origin Resource Sharing)
# This is crucial for allowing a web frontend to communicate with this backend.
# For development, we allow all origins. For production, this should be restricted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Database Connection Events ---
# These events will run when the application starts and shuts down.
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown") 
async def shutdown_db_client():
    await close_mongo_connection()


# --- API Routers ---
# Include the routers from the api module.
# Each router handles a specific part of the API (e.g., authentication, chat).
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Agent"])
app.include_router(user_settings.router, prefix="/api/user", tags=["User Settings"])
app.include_router(jars.router, prefix="/api/jars", tags=["Jar Management"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transaction Management"])
app.include_router(fees.router, prefix="/api/fees", tags=["Fee Management"])
app.include_router(plans.router, prefix="/api/plans", tags=["Plan Management"])


# --- Root Endpoint ---
# A simple endpoint to check if the API is running.
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint for health check.
    """
    return {"status": "ok", "message": "Welcome to the VPBank AI Financial Coach API"}