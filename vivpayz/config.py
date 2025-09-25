import os

class Config:
    SECRET_KEY       = os.getenv("SECRET_KEY", "f1d4f827b1b20447d728937fd97ce9f6ea5a11f3983031601d76dc10d9d355e6")
    JWT_SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "14a00573ba041e0db5bb8cb552e5cd0c1fdd512d0c68deb57c4a3913563c86a0")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")

 #   SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
