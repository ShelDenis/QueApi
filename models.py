from sqlalchemy import Column, Integer, String, Date, Time, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base, mapped_column

Base = declarative_base()


class User(Base):
    __tablename__ = "QUser"

    u_id = Column(Integer, primary_key=True, index=True)
    u_name = Column(String)
    u_surname = Column(String)
    u_mail = Column(String, unique=True, index=True)
    u_pswrd = Column(String)
    u_ava = Column(String)

    created_queues = relationship(
        "Queue",
        back_populates="creator",
        cascade="all, delete-orphan",
        lazy="select"
    )


class Queue(Base):
    __tablename__ = "Queue"

    q_id = Column(Integer, primary_key=True, index=True)
    q_name = Column(String)
    q_creation_date = Column(Date)

    q_creator_id = Column(Integer, ForeignKey("QUser.u_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    q_sequence = Column(JSON)
    q_img_path = Column(String)
    q_describe = Column(String)

    creator = relationship(
        "User",
        back_populates="created_queues"
    )


class ChatMessage(Base):
    __tablename__ = "ChatMessage"

    m_id = Column(Integer, primary_key=True, index=True)
    q_id = Column(Integer, ForeignKey("Queue.q_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    u_id = Column(Integer, ForeignKey("QUser.u_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    m_text = Column(String)
    m_date = Column(Date)
    m_time = Column(Time)

    queue = relationship("Queue", back_populates="messages")
    user = relationship("QUser", back_populates="messages")