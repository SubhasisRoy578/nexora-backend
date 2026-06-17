from sqlalchemy import (
    Column,
    String,
    Integer
)

from app.database.database import Base


class AgentScore(Base):

    __tablename__ = "agent_scores"

    agent_name = Column(
        String,
        primary_key=True
    )

    successes = Column(
        Integer,
        default=0
    )

    failures = Column(
        Integer,
        default=0
    )

    score = Column(
        Integer,
        default=0
    )