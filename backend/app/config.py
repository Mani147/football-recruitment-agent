import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Football AI Scout & Recruitment Decision Support System"
    API_V1_STR: str = "/api"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_EMBEDDING_MODEL: str = "gemini-embedding-2-preview"
    DEFAULT_LLM_MODEL: str = "gemini-2.5-flash"
    DATABASE_PATH: str = str(os.path.join(os.path.dirname(__file__), "data", "football_scout.db"))

settings = Settings()
