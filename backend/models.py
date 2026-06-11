from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from sqlalchemy import event # <--- 1. IMPORT THIS
from sqlalchemy.engine import Engine # <--- 2. IMPORT THIS

from sqlalchemy.pool import NullPool  # 🚀 1. IMPORT THIS

DATABASE_URL = "sqlite:///./aegis_core.db"
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 60},
    poolclass=NullPool  
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
    
    


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String) 
    hashed_password = Column(String) 
    full_name = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    incidents = relationship("Incident", back_populates="owner")
    chat_sessions = relationship("ChatSession", back_populates="owner")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    raw_logs = Column(Text) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="open")
    anomaly_description = Column(Text)
    root_cause = Column(Text)
    remediation_action = Column(Text)
    remediation_status = Column(String, default="pending")
    
    owner = relationship("User", back_populates="incidents")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Incident Discussion")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")

# --- NEW: QA Escalation Ticket Model ---
class EscalationTicket(Base):
    __tablename__ = "escalation_tickets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    status = Column(String, default="open") # "open" or "resolved"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", backref="tickets")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()