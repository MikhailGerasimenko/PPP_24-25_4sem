from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.bruteforce import router

app = FastAPI(title="Bruteforce API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер для брутфорса
app.include_router(router, prefix="")

@app.get("/")
async def root():
    return {"message": "Bruteforce API работает!"} 