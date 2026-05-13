from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from loguru import logger

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import setup_exception_handlers as register_exceptions
from app.core.rate_limit import setup_rate_limit
from app.core.database import dispose_engine

def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI instance.
    """
    # Initialize Logging
    setup_logging()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Advanced Agentic Backend for pgagi",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure Middleware
    setup_middleware(app)

    # Configure Rate Limiting
    setup_rate_limit(app)

    # Configure Routers
    setup_routers(app)

    # Configure Exception Handlers
    setup_exception_handlers(app)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up pgagi API...")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down pgagi API...")
        await dispose_engine()

    return app

def setup_middleware(app: FastAPI) -> None:
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request ID tracking
    app.add_middleware(CorrelationIdMiddleware)

    # Logging Middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        from asgi_correlation_id import correlation_id
        
        # Add correlation ID to loguru context
        with logger.contextualize(request_id=correlation_id.get()):
            logger.info(f"Incoming request: {request.method} {request.url.path}")
            try:
                response = await call_next(request)
                logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
                return response
            except Exception as e:
                logger.exception(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}")
                raise

def setup_routers(app: FastAPI) -> None:
    # Main API router for v1
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Root endpoint
    @app.get("/", tags=["System"])
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "docs": "/docs",
            "status": "active",
            "version": settings.VERSION
        }

def setup_exception_handlers(app: FastAPI) -> None:
    # Register global exception handlers
    register_exceptions(app)

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)