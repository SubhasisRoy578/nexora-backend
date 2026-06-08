from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, nullable=False)

    full_name = Column(String)

    image_url = Column(String)

    hashed_password = Column(String)

    provider = Column(String, default="google")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )