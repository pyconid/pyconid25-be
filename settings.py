import os
from core.log import logger

if os.environ.get("ENVIRONTMENT") != "os":
    logger.info("load env from file")
    from dotenv import load_dotenv

    load_dotenv()
else:
    logger.info("load env from os")


def str_to_bool(string: str) -> bool:
    if string in ["true", "TRUE", "True"]:
        return True
    elif string in ["false", "FALSE", "False"]:
        return False
    else:
        raise Exception(
            f"{string} is not boolean, ex input true -> true, True, TRUE, ex input false -> false, False, FALSE"
        )


# Environtment
ENVIRONTMENT = os.environ.get("ENVIRONTMENT")

# Deployment mode
DEPLOYMENT_MODE = os.environ.get("DEPLOYMENT_MODE", "development")

# JWT conf
JWT_PREFIX = os.environ.get("JWT_PREFIX", "Bearer")
SECRET_KEY = os.environ.get("SECRET_KEY", "pyconid25_secret")
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

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

# MAIL conf
MAIL_DYNAMIC = str_to_bool(os.environ.get("MAIL_DYNAMIC", "False"))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "test@example.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "465"))
MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "")
MAIL_TLS = str_to_bool(os.environ.get("MAIL_TLS", "False"))
MAIL_SSL = str_to_bool(os.environ.get("MAIL_SSL", "True"))
USE_CREDENTIALS = str_to_bool(os.environ.get("USE_CREDENTIALS", "True"))
