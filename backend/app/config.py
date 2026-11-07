import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Touchline Historical Football Analysis"
    API_V1_STR: str = "/api"
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "data", "football_scout.db"))

settings = Settings()
