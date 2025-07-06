from core.log import logger
from settings import POSTGRES_HOST, POSTGRES_PORT
from models import db


def health_check():
    logger.info("run app with")
    logger.info(f"postgres host = {POSTGRES_HOST}")
    logger.info(f"postgres port = {POSTGRES_PORT}")
    logger.info("try echo postgres db")
    with db() as session:
        logger.info(not session.connection().closed)
    logger.info("successfully connect to postgres")
