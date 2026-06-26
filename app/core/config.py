import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "mysql+aiomysql://root@localhost:3306/db_neuropalm")
    secret_key: str = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "default_secret_key_replace_in_production"
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "30")
    
    argon2_time_cost: int = int(os.getenv("ARGON2_TIME_COST") or "2")
    argon2_memory_cost: int = int(os.getenv("ARGON2_MEMORY_COST") or "102400")
    argon2_parallelism: int = int(os.getenv("ARGON2_PARALLELISM") or "8")
    argon2_hash_len: int = int(os.getenv("ARGON2_HASH_LEN") or "16")
    
    class Config:
        env_file = ".env"

settings = Settings()