from sqlalchemy.orm import Session

from app.database.database import SessionLocal

from app.database.models.agent_score import (
    AgentScore
)


class AgentScoreRepository:

    def get(
        self,
        agent_name
    ):

        db: Session = SessionLocal()

        try:

            return (
                db.query(
                    AgentScore
                )
                .filter(
                    AgentScore.agent_name
                    == agent_name
                )
                .first()
            )

        finally:

            db.close()


agent_score_repository = (
    AgentScoreRepository()
)