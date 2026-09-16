import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.database import get_db_connection
from src.api.routers.companies import router as companies_router
from src.api.routers.pl import router as pl_router
from src.api.routers.bs import router as bs_router
from src.api.routers.cashflow import router as cashflow_router
from src.api.routers.ratios import router as ratios_router
from src.api.routers.tearsheet import router as tearsheet_router
from src.api.routers.screener import router as screener_router
from src.api.routers.sectors import router as sectors_router
from src.api.routers.peers import router as peers_router
from src.api.routers.valuation import router as valuation_router
from src.api.routers.market_cap import router as market_cap_router
from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.documents import router as documents_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Nifty100 Financial Intelligence API",
    description="REST API for the Nifty100 Financial Intelligence Platform",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Check API and database health."""
    try:
        connection = get_db_connection()
        connection.execute("SELECT 1")
        connection.close()

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as exc:
        logger.exception("Database health check failed")

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }


@app.get("/", tags=["Health"])
def root():
    """API welcome endpoint."""
    return {
        "message": "Nifty100 Financial Intelligence API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


app.include_router(
    companies_router,
    prefix="/api/v1",
    tags=["Companies"],
)

app.include_router(
    pl_router,
    prefix="/api/v1",
    tags=["Profit & Loss"],
)

app.include_router(
    bs_router,
    prefix="/api/v1",
    tags=["Balance Sheet"],
)

app.include_router(
    cashflow_router,
    prefix="/api/v1",
    tags=["Cash Flow"],
)

app.include_router(
    ratios_router,
    prefix="/api/v1",
    tags=["Financial Ratios"],
)

app.include_router(
    tearsheet_router,
    prefix="/api/v1",
    tags=["Tearsheet"],
)

app.include_router(
    screener_router,
    prefix="/api/v1",
    tags=["Screener"],
)

app.include_router(
    sectors_router,
    prefix="/api/v1",
    tags=["Sectors"],
)

app.include_router(
    peers_router,
    prefix="/api/v1",
    tags=["Peers"],
)

app.include_router(
    valuation_router,
    prefix="/api/v1",
    tags=["Valuation"],
)

app.include_router(
    market_cap_router,
    prefix="/api/v1",
    tags=["Market Cap"],
)

app.include_router(
    portfolio_router,
    prefix="/api/v1",
    tags=["Portfolio"],
)

app.include_router(
    documents_router,
    prefix="/api/v1",
    tags=["Documents"],
)
