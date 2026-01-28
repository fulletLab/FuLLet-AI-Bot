from sqlalchemy import create_engine, Column, String, Integer, BigInteger, Float, LargeBinary
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
import os
import time


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    DB_PATH = "sqlite:///database/bot_data.db"
else:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    DB_PATH = DATABASE_URL

class Base(DeclarativeBase):
    pass

class UserSession(Base):
    __tablename__ = "sessions"
    user_id = Column(String, primary_key=True)
    channel_id = Column(BigInteger)
    last_img_name = Column(String, nullable=True)
    last_img_bytes = Column(LargeBinary, nullable=True)
    updated_at = Column(Float, default=time.time, onupdate=time.time)

class GlobalCounter(Base):
    __tablename__ = "counters"
    name = Column(String, primary_key=True)
    value = Column(Integer, default=0)

if DB_PATH.startswith("sqlite"):
    engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_PATH, poolclass=NullPool, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)

def init_db():

    """Initialize database, creating tables and default records if needed."""

    if DB_PATH.startswith("sqlite"):
        db_dir = "database"
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

    Base.metadata.create_all(engine)
    
    with SessionLocal() as session:
        if not session.get(GlobalCounter, "image_count"):
            session.add(GlobalCounter(name="image_count", value=0))
            session.commit()

def get_db_session(user_id):
    with SessionLocal() as session:
        return session.get(UserSession, str(user_id))

def save_db_session(user_id, channel_id, img_bytes=None, img_name=None):
    with SessionLocal() as session:
        s = session.get(UserSession, str(user_id))
        if not s:
            s = UserSession(user_id=str(user_id), channel_id=channel_id, updated_at=time.time())
        else:
            s.channel_id = channel_id
            s.updated_at = time.time()
            
        s.last_img_bytes = img_bytes
        s.last_img_name = img_name
            
        session.merge(s)
        session.commit()

def delete_db_session(channel_id):
    with SessionLocal() as session:
        session.query(UserSession).filter(UserSession.channel_id == channel_id).delete()
        session.commit()

def get_next_image_index():
    with SessionLocal() as session:
        counter = session.get(GlobalCounter, "image_count")
        counter.value += 1
        val = counter.value
        session.commit()
        return val

init_db()
