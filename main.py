from fastapi import FastAPI
from api.routes import router
from core.worker import start_worker

app = FastAPI(
    title="LLM Code Deploy API",
    description="Backend API for AI task queue and static site generation",
    version="1.0.0"
)

# Include API routes (e.g., /api/task, /health)
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    try:
        await start_worker()
        print("✅ Background worker started successfully.")
    except Exception as e:
        print(f"⚠️ Worker startup failed: {e}")

@app.get("/")
def root():
    return {"message": "Welcome to the LLM Code Deploy API!"}
