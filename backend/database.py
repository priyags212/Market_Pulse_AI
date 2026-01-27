from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt
import os
from datetime import datetime

DATABASE_URL = "sqlite:///./marketpulse.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    dob = Column(String, nullable=True) # Storing as string YYYY-MM-DD for simplicity

    watchlist = relationship("WatchlistItem", back_populates="owner")

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String)
    name = Column(String)

    owner = relationship("User", back_populates="watchlist")

class NewsAnalytics(Base):
    __tablename__ = "news_analytics"

    id = Column(Integer, primary_key=True, index=True)
    news_link = Column(String, unique=True, index=True)
    views = Column(Integer, default=0)

class SentNotification(Base):
    __tablename__ = "sent_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    article_link = Column(String, index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)

    # We want to ensure a user doesn't get the same link twice
    # But SQLite doesn't support complex unique constraints easily in this declarative style without Table args
    # For now, we'll handle unique checks in logic or add a UniqueConstraint if needed.


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    link = Column(String, unique=True, index=True)
    image_url = Column(String, nullable=True)
    source = Column(String, default="Moneycontrol")
    timestamp = Column(DateTime, index=True)
    category = Column(String, index=True)
    sentiment = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
