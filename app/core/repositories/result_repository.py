from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity


class ResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(self, aggregated_result: AggregatedResultEntity) -> None:
        self.session.add(aggregated_result)
        self.session.commit()
