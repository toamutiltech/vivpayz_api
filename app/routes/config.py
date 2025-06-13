import os

class Config:
    SECRET_KEY       = os.getenv("SECRET_KEY", "change-this!")
    JWT_SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "jwt-change-this!")
