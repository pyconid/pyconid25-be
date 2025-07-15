from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.health_check import health_check
from core.log import logger
from routes.auth import router as auth_router
from starlette.middleware.sessions import SessionMiddleware

from settings import ENVIRONTMENT, SECRET_KEY

health_check()


app = FastAPI(title="PyconId 2025 BE")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=ENVIRONTMENT == "prod" or ENVIRONTMENT == "production",
    max_age=1800,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
async def hello():
    logger.info("hello")
    return {"Hello": "from pyconid 2025 BE"}
