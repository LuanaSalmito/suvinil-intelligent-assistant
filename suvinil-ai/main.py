
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, users, paints, ai_chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events da aplicação"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Suvinil AI API",
    description="API para Catálogo Inteligente de Tintas com IA",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(paints.router, prefix="/paints", tags=["Paints"])
app.include_router(ai_chat.router, prefix="/ai", tags=["AI Chat"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "suvinil-ai-api"}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Suvinil AI API - Catálogo Inteligente de Tintas",
        "docs": "/docs",
        "version": "1.0.0"
    }
