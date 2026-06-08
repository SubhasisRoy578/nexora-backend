from sqlalchemy import Column, Integer, String, Text

from app.database import Base


class ChatHistory(Base):

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)

    role = Column(String)

    content = Column(Text)