from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.routers import router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/")
def hello():
    """Welcome message"""
    return {"message": f"Welcome to {settings.app_name}"}


# Include routers
app.include_router(router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
