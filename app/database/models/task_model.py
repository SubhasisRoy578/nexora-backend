from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime

from datetime import datetime

from app.database.database import Base


class AgentTask(Base):

    __tablename__ = "agent_tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    task_id = Column(
        String,
        unique=True,
        index=True
    )

    user_id = Column(
        String,
        index=True
    )

    goal = Column(Text)

    status = Column(
        String,
        default="pending"
    )

    result = Column(
        Text,
        nullable=True
    )

    error = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at = Column(
        DateTime,
        nullable=True
    )