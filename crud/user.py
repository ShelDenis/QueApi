from sqlalchemy.orm import Session
from sqlalchemy import select
from models import User
from schemas import UserRegister
from auth import get_password_hash, verify_password
import re

def validate_email(email: str) -> bool:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def create_user(db: Session, user_data: UserRegister):
    if not validate_email(user_data.u_mail):
        raise ValueError("Неверный формат email")
    
    existing = db.execute(select(User).where(User.u_mail == user_data.u_mail)).scalar_one_or_none()
    if existing:
        raise ValueError("Пользователь с таким email уже существует")
    
    new_user = User(
        u_name=user_data.u_name,
        u_surname=user_data.u_surname,
        u_mail=user_data.u_mail,
        u_pswrd=get_password_hash(str(user_data.u_pswrd)),
    )
    
    db.add(new_user)
    db.flush()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.execute(select(User).where(User.u_mail == email)).scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.u_pswrd):
        return None
    return user

def get_user_by_id(db: Session, user_id: int):
    return db.execute(select(User).where(User.u_id == user_id)).scalar_one_or_none()