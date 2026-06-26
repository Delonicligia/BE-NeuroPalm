import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL")
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    
    argon2_time_cost: int = int(os.getenv("ARGON2_TIME_COST"))
    argon2_memory_cost: int = int(os.getenv("ARGON2_MEMORY_COST"))
    argon2_parallelism: int = int(os.getenv("ARGON2_PARALLELISM"))
    argon2_hash_len: int = int(os.getenv("ARGON2_HASH_LEN"))
    
    class Config:
        env_file = ".env"

settings = Settings()