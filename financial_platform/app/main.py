"""
T9: Exception handling middleware + güvenlik header'ları.
"""
import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import Base, engine
from app.utils.logging import logger, log_exception
from app.api.v1 import auth, companies, financial, admin, subscriptions, notifications, extended

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Analysis Platform API",
    description="Finansal veri yönetimi, AI destekli OCR ve analiz platformu.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_origins = list(settings.ALLOWED_ORIGINS)
if settings.DEBUG and "null" not in _origins:
    _origins.append("null")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Disposition"],
    max_age=600,
)


# ── Güvenlik Header'ları Middleware ───────────────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "img-src 'self' https://ui-avatars.com data:;"
        )
    return response


# ── İstek Loglama + Hata Yakalama Middleware ──────────────────────────────────
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.time() - start) * 1000, 2),
        )
        return response
    except SQLAlchemyError as exc:
        log_exception(exc, {"path": request.url.path, "method": request.method})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Veritabanı hatası oluştu. Lütfen daha sonra deneyin."},
        )
    except Exception as exc:
        log_exception(exc, {"path": request.url.path, "method": request.method})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Beklenmeyen bir hata oluştu. Lütfen daha sonra deneyin."},
        )


# ── Router'lar ────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(financial.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(extended.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
