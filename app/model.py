from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field, DateTime

# Database Model
class Results(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: DateTime = Field(default_factory=datetime.now)
    request: str
    result: str
