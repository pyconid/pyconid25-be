import os
from core.log import logger

if os.environ.get("ENVIRONTMENT") != "os":
    logger.info("load env from file")
    from dotenv import load_dotenv

    load_dotenv()
else:
    logger.info("load env from os")

# Environtment
ENVIRONTMENT = os.environ.get("ENVIRONTMENT")

# JWT conf
JWT_PREFIX = os.environ.get("JWT_PREFIX", "Bearer")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
if ACCESS_TOKEN_EXPIRE_MINUTES is not None:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_MINUTES = os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", 60)
if REFRESH_TOKEN_EXPIRE_MINUTES is not None:
    REFRESH_TOKEN_EXPIRE_MINUTES = int(REFRESH_TOKEN_EXPIRE_MINUTES)

# Timezone
TZ = os.environ.get("TZ", "Asia/Jakarta")

# Postgresql conf
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE")

FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL")

# Oauth
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
