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


class UserRegister(BaseModel):
    u_name: str
    u_surname: str
    u_mail: str
    u_pswrd: str

class UserLogin(BaseModel):
    u_mail: str
    u_pswrd: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_name: str

class UserResponse(BaseModel):
    u_id: int
    u_name: str
    u_surname: str
    u_mail: str
    
    class Config:
        from_attributes = True