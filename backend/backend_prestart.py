from sqlalchemy import Engine, text
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_fixed

from app.db import get_engine


@retry(
    stop=stop_after_attempt(60 * 2),  # Try for 2 minutes
    wait=wait_fixed(1),  # Wait one second per try
)
def init(engine: Engine) -> None:
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        print("Failed to contact the database")
        raise e


def main() -> None:
    init(get_engine())


if __name__ == "__main__":
    main()
