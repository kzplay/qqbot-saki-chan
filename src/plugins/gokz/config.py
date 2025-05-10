import os

from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")


class Config(BaseModel):
    """Plugin Config Here"""
    steam_api_key: str = STEAM_API_KEY
