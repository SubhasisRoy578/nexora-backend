from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer)

    storage_path = Column(String)

    uploaded_at = Column(DateTime, default=datetime.utcnow)