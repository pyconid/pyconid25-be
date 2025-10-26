from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from core.health_check import health_check
from core.log import logger
from routes.auth import router as auth_router
from routes.user_profile import router as user_profile_router
from routes.locations import router as locations_router
from routes.ticket import router as ticket_router
from routes.payment import router as payment_router


health_check()

app = FastAPI(title="PyconId 2025 BE")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_profile_router)
app.include_router(locations_router)
app.include_router(ticket_router)
app.include_router(payment_router)


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    # Logikanya hampir sama, hanya cara mengambil detail errornya sedikit berbeda
    error_details = []
    # exc.errors() dari pydantic.ValidationError sedikit berbeda strukturnya
    for error in exc.errors():
        field = error["loc"][0] if error["loc"] else "general"
        message = error["msg"]
        error_details.append({"field": field, "message": message})

    return JSONResponse(
        status_code=422,
        content={
            "message": "Terjadi kesalahan validasi pada data form (Pydantic validation).",
            "errors": error_details,
        },
    )


@app.get("/")
async def hello():
    logger.info("hello")
    return {"Hello": "from pyconid 2025 BE"}


@app.get("/health")
def health():
    return {"status": "ok"}
