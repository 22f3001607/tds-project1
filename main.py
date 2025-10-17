from fastapi import FastAPI
from api.routes import router
from core.worker import start_worker

app = FastAPI(title="LLM Code Deploy API")
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    await start_worker()
    print("Background worker started.")
