from sqlalchemy import Column, Integer, String, Date, Time, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import date, datetime  

class User(Base):
    __tablename__ = "QUser"
    
    u_id = Column(Integer, primary_key=True, autoincrement=True)
    u_name = Column(String)
    u_surname = Column(String)
    u_mail = Column(String, unique=True, index=True)
    u_pswrd = Column(String)
    u_ava = Column(String, nullable=True)
    
    created_queues = relationship("Queue", back_populates="creator")

class Queue(Base):
    __tablename__ = "Queue"
    
    q_id = Column(Integer, primary_key=True, autoincrement=True)
    q_name = Column(String)
    q_creation_date = Column(Date, default=date.today)
    q_creator_id = Column(Integer, ForeignKey("QUser.u_id"))
    q_sequence = Column(JSON, default=list)
    q_img_path = Column(String, nullable=True)
    q_describe = Column(String, nullable=True)
    last_activity = Column(DateTime, default=datetime.now, onupdate=datetime.now)  
    
    creator = relationship("User", back_populates="created_queues")

class ChatMessage(Base):
    __tablename__ = "ChatMessage"
    
    m_id = Column(Integer, primary_key=True, autoincrement=True)
    q_id = Column(Integer, ForeignKey("Queue.q_id"))
    u_id = Column(Integer, ForeignKey("QUser.u_id"))
    m_text = Column(String)
    m_date = Column(Date, default=date.today)
    m_time = Column(Time)