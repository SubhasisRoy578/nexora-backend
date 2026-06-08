from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.database.database import Base


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    memory_type = Column(Text)

    content = Column(Text)

    embedding_id = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )