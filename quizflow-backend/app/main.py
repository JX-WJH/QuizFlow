# app/main.py (更新部分)
from fastapi import FastAPI
from app.api.v1.endpoints import router as api_v1_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 注册 API 路由，并添加前缀 v1
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
