from fastapi import FastAPI
from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="Pipeline Automation SaaS API",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "ok", "message": "B2B SaaS API is running!"}