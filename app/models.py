from sqlalchemy import Column, Integer, String, Boolean, Text
from .database import Base

# --- Existing example model (kept) ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)

# --- New minimal models for Milestone C ---

class Code(Base):
    __tablename__ = "codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)   # e.g., "19928"
    name = Column(String(200), nullable=False)                           # short label
    description = Column(Text, nullable=True)                            # optional long text
    is_active = Column(Boolean, nullable=False, default=True)

class Establishment(Base):
    __tablename__ = "establishments"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), nullable=False, index=True)              # e.g., "54055"
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=True)
    region_code = Column(String(5), nullable=True)                       # e.g., "08"
    is_active = Column(Boolean, nullable=False, default=True)

class Context(Base):
    __tablename__ = "contexts"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)   # e.g., "after_hours"
    value = Column(String(200), nullable=False)                           # e.g., "Y"
    description = Column(Text, nullable=True)
