from pydantic import BaseModel

class CodeOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    is_active: bool

    # Pydantic v2: allow reading from SQLAlchemy objects
    model_config = {"from_attributes": True}
from pydantic import BaseModel

class ContextOut(BaseModel):
    id: int
    key: str
    value: str
    description: str | None = None
    model_config = {"from_attributes": True}

class EstablishmentOut(BaseModel):
    id: int
    number: str
    name: str
    city: str | None = None
    region_code: str | None = None
    is_active: bool
    model_config = {"from_attributes": True}
