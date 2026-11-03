import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .database import engine, Base
from .schemas import HealthResponse
from .api.reviews import router as reviews_router
from .api.demo import router as demo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"AP Agent started. CORS origins: {settings.cors_origins}")
    yield
    # Shutdown
    logger.info("AP Agent shutting down...")


app = FastAPI(
    title="AP Agent API",
    description="Accounts Payable Autonomous Audit & Discrepancy Detection Agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(reviews_router, prefix="/api")
app.include_router(demo_router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        database="connected"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please check logs for details."}
    )

