"""FastAPI application factory and configuration.

This module initializes the FastAPI application, configures middleware
(CORS, logging), registers routes, and sets up exception handlers.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sys
import os

from core.config import settings
from core.logger import get_logger
from routers import chat
from routers import tts

current_dir = os.path.dirname(os.path.abspath(__file__))

# Lấy đường dẫn của thư mục cha (thư mục root dự án)
parent_dir = os.path.dirname(current_dir)

# Thêm thư mục root vào sys.path để Python có thể tìm thấy llm_core
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    
# Initialize logger for main module
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Initializes services at application startup and cleans up at shutdown.
    Initializes: SenseiAgent (LLM core), VoicevoxTTSService (audio synthesis).

    Args:
        app: FastAPI application instance
    """
    # ========== STARTUP ==========
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"CORS enabled for origins: {settings.cors_origins}")
    
    # Initialize SenseiAgent for chat processing
    try:
        from llm_core import SenseiAgent
        
        # Determine config path (relative to backend directory)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(backend_dir, "..", "config.yaml")
        
        logger.info(f"Initializing SenseiAgent with config: {config_path}")
        agent = SenseiAgent(config_path=config_path)
        
        # Store agent in app state for route handlers to access
        app.state.sensei_agent = agent
        logger.info("SenseiAgent initialized successfully and ready for chat processing")
        
    except Exception as e:
        logger.error(f"Failed to initialize SenseiAgent: {e}", exc_info=True)
        logger.warning("Chat endpoint will be unavailable. Ensure GOOGLE_API_KEY is set and config.yaml exists.")
        app.state.sensei_agent = None
    
    # Initialize Voicevox TTS Service
    try:
        from tts.voicevox_service import VoicevoxTTSService
        
        logger.info("Initializing Voicevox TTS service with real-time auto-play")
        # auto_play=True enables in-memory audio playback (requires sounddevice)
        tts_service = VoicevoxTTSService(auto_play=True)
        
        # Start the TTS engine with polling mechanism
        if tts_service.start_engine(timeout=30):
            app.state.tts_service = tts_service
            logger.info(
                "Voicevox TTS engine started successfully and ready for real-time synthesis"
            )
        else:
            logger.warning("Failed to start Voicevox TTS engine. TTS endpoint will be unavailable.")
            app.state.tts_service = tts_service  # Store anyway for error handling
        
    except Exception as e:
        logger.error(f"Failed to initialize TTS service: {e}", exc_info=True)
        logger.warning("TTS endpoint will be unavailable.")
        app.state.tts_service = None
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info(f"Shutting down {settings.app_name}")
    
    # Clean up TTS service
    if hasattr(app.state, "tts_service") and app.state.tts_service:
        try:
            app.state.tts_service.stop_engine()
            logger.info("Voicevox TTS engine stopped")
        except Exception as e:
            logger.error(f"Error stopping TTS engine: {e}")
    
    # Clean up LLM service
    if hasattr(app.state, "sensei_agent") and app.state.sensei_agent:
        logger.info("SenseiAgent resources cleaned up")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory function sets up:
    - CORS middleware for frontend communication
    - Request/response middleware
    - Exception handlers
    - Route registration
    - Startup/shutdown lifespan

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for AI NARAGI chat interface",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # ==================== MIDDLEWARE SETUP ====================

    # CORS Middleware - Allow frontend to make requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    # ==================== EXCEPTION HANDLERS ====================

    @app.exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY)
    async def validation_exception_handler(request: Request, exc: Exception):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Request validation failed",
                "detail": str(exc)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all exception handler for unhandled errors."""
        logger.error(
            f"Unhandled exception on {request.url.path}: {str(exc)}",
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": "An unexpected error occurred. Please try again."
            }
        )

    # ==================== ROUTE REGISTRATION ====================

    # Include chat routes
    app.include_router(chat.router)
    
    # Include TTS routes
    app.include_router(tts.router)

    logger.info("FastAPI application created and configured successfully")
    return app


# Create the application instance
app = create_app()


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting Uvicorn server on {settings.server_host}:{settings.server_port}"
    )

    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )