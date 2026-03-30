
class ResultRepository:
    def __init__(self, db: object) -> None:  # todo: change db: object to db: Session when we have a db
        self._db = db
