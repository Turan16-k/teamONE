"""
T9: Exception handling middleware - kullanıcıya clean mesaj, mühendise stack trace.
"""
import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import Base, engine
from app.utils.logging import logger, log_exception
from app.api.v1 import auth, companies, financial, admin, subscriptions, notifications

# Uygulama başlarken tabloları oluştur (production'da alembic migrations kullanın)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Analysis Platform API",
    description="Finansal veri yönetimi, AI destekli OCR ve analiz platformu.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
_origins = settings.ALLOWED_ORIGINS
# Geliştirme ortamında file:// protokolü için "null" origin'e izin ver
if settings.DEBUG and "null" not in _origins:
    _origins = list(_origins) + ["null"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """T9: Her isteği logla; hata olursa stack trace sakla, kullanıcıya clean yanıt ver."""
    start = time.time()
    response = None
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
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


# Router'ları kaydet
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(financial.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0"}
