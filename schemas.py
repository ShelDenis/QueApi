from pydantic import BaseModel
from typing import Optional
#
class QueueCreate(BaseModel):
    q_name: str
    q_describe: Optional[str] = None
    q_img_path: Optional[str] = None

class QueueResponse(BaseModel):
    q_id: int
    q_name: str
    q_describe: Optional[str] = None
    q_img_path: Optional[str] = None
    
    class Config:
        from_attributes = True

class JoinQueueRequest(BaseModel):
    user_id: int



class MessageCreate(BaseModel):
    queue_id: int
    user_id: int
    text: str

class MessageResponse(BaseModel):
    m_id: int
    queue_id: int
    user_id: int
    text: str
    m_date: str
    m_time: str
    
    class Config:
        from_attributes = True