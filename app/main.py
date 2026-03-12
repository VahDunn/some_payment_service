from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.core.domain.exceptions import AppError

app = FastAPI(title="Orders Payments Service")

app.include_router(orders_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )