# get env variables
import os
# python-dotenv
from dotenv import load_dotenv
load_dotenv(".env")
class Env:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "1q2w3e4r!")
    DB_NAME: str = os.getenv("DB_NAME", "PUZZLE")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    RECORD_API_KEY: str = os.getenv("RECORD_API_KEY", "")
