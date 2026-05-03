from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from schemas import (
    QueueCreate, QueueResponse,
    MessageCreate, MessageResponse,
    UserRegister, UserLogin, Token, UserResponse
)
from crud.queue import create_queue, add_to_queue, leave_queue, rejoin_queue, send_message, get_queue_messages
from crud.user import create_user, authenticate_user, get_user_by_id
from auth import create_access_token, decode_access_token
from models import Queue
from sqlalchemy import select


from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from database import get_db, engine, Base
from crud.queue import cleanup_empty_queues



def run_cleanup():
    #Запускает очистку пустых очередей
    from database import SessionLocal
    db = SessionLocal()
    try:
        deleted = cleanup_empty_queues(db)
        if deleted > 0:
            print(f" Удалено {deleted} пустых очередей (неактивны более 10 минут)")
    except Exception as e:
        print(f" Ошибка очистки: {e}")
    finally:
        db.close()

# Настройка фонового планировщика
scheduler = BackgroundScheduler()
scheduler.add_job(run_cleanup, 'interval', minutes=1)  # Проверка каждую минуту

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск при старте
    scheduler.start()
    print(" Планировщик очистки очередей запущен")
    yield
    # Остановка при завершении
    scheduler.shutdown()
    print(" Планировщик очистки остановлен")

app = FastAPI(title="QueLab API", lifespan=lifespan)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="QueLab API")
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Неверный токен")
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

@app.get("/")
def root():
    return {"message": "QueLab API работает"}

@app.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        return create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.u_mail, user_data.u_pswrd)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token(data={"sub": str(user.u_id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.u_id,
        "user_name": f"{user.u_name} {user.u_surname}"
    }

@app.post("/queues", response_model=QueueResponse)
def create_queue_endpoint(queue_data: QueueCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return create_queue(db, queue_data, current_user.u_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/queues")
def get_all_queues(db: Session = Depends(get_db)):
    #Получить все очереди
    queues = db.execute(select(Queue)).scalars().all()
    return [
        {
            "q_id": q.q_id,
            "q_name": q.q_name,
            "q_describe": q.q_describe,
            "q_creator_id": q.q_creator_id,
            "participants_count": len(q.q_sequence) if q.q_sequence else 0
        }
        for q in queues
    ]


@app.get("/queues/{queue_id}/status")
def get_queue_status(queue_id: int, db: Session = Depends(get_db)):
    #Получить актуальное состояние очереди
    from crud.queue import get_queue_by_id
    queue = get_queue_by_id(db, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Очередь не найдена")
    return queue

@app.get("/queues/{queue_id}")
def get_queue(queue_id: int, db: Session = Depends(get_db)):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Очередь не найдена")
    return {
        "q_id": queue.q_id,
        "q_name": queue.q_name,
        "q_describe": queue.q_describe,
        "q_creator_id": queue.q_creator_id,
        "participants_count": len(queue.q_sequence) if queue.q_sequence else 0,
        "participants": queue.q_sequence if queue.q_sequence else []
    }

@app.get("/users/me/queues")
def get_my_queues(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    all_queues = db.execute(select(Queue)).scalars().all()
    
    result = []
    for q in all_queues:
        q_sequence = q.q_sequence if q.q_sequence else []
        is_member = current_user.u_id in q_sequence
        is_creator = q.q_creator_id == current_user.u_id
        
        if is_member or is_creator:
            position = None
            if is_member:
                position = q_sequence.index(current_user.u_id) + 1
            
            result.append({
                "q_id": q.q_id,
                "q_name": q.q_name,
                "q_describe": q.q_describe,
                "participants_count": len(q_sequence),
                "your_position": position,
                "is_creator": is_creator
            })
    return result

@app.post("/queues/{queue_id}/join")
def join_queue(queue_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = add_to_queue(db, queue_id, current_user.u_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/queues/{queue_id}/leave")
def leave_queue_endpoint(queue_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = leave_queue(db, queue_id, current_user.u_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/queues/{queue_id}/rejoin")
def rejoin_queue_endpoint(queue_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = rejoin_queue(db, queue_id, current_user.u_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/messages", response_model=MessageResponse)
def send_message_endpoint(message: MessageCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if message.user_id != current_user.u_id:
        raise HTTPException(status_code=403, detail="Нельзя отправлять сообщения от имени другого пользователя")
    try:
        result = send_message(db, message.queue_id, message.user_id, message.text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/queues/{queue_id}/messages")
def get_messages_endpoint(queue_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = get_queue_messages(db, queue_id, current_user.u_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@app.get("/queues/{queue_id}/participants")
def get_queue_participants(queue_id: int, db: Session = Depends(get_db)):
    #Получить список участников очереди с порядковыми номерами
    from models import Queue, User
    from sqlalchemy import select
    
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Очередь не найдена")
    
    participants_list = queue.q_sequence if queue.q_sequence else []
    
    result = []
    for position, user_id in enumerate(participants_list, start=1):
        user = db.execute(select(User).where(User.u_id == user_id)).scalar_one_or_none()
        if user:
            result.append({
                "position": position,
                "user_id": user.u_id,
                "user_name": f"{user.u_name} {user.u_surname}",
                "is_creator": queue.q_creator_id == user.u_id
            })
    
    # Добавляем создателя, если его нет в списке
    if queue.q_creator_id not in participants_list:
        creator = db.execute(select(User).where(User.u_id == queue.q_creator_id)).scalar_one_or_none()
        if creator:
            result.insert(0, {
                "position": 0,
                "user_id": creator.u_id,
                "user_name": f"{creator.u_name} {creator.u_surname} (создатель)",
                "is_creator": True
            })
    
    return result



from fastapi import File, UploadFile
import shutil
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/queues/{queue_id}/upload-avatar")
async def upload_queue_avatar(
    queue_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #Загрузить аватарку для очереди (только создатель)
    from models import Queue
    from sqlalchemy import select
    
    # Проверяем существование очереди
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Очередь не найдена")
    
    # Проверяем, что пользователь - создатель очереди
    if queue.q_creator_id != current_user.u_id:
        raise HTTPException(status_code=403, detail="Только создатель очереди может менять аватарку")
    
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Поддерживаются только JPEG, PNG, GIF, WEBP")
    
    # Создаем уникальное имя файла
    file_extension = file.filename.split(".")[-1]
    new_filename = f"queue_{queue_id}_{int(datetime.now().timestamp())}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {e}")
    
    # Обновляем путь в базе данных
    queue.q_img_path = f"/uploads/{new_filename}"
    db.add(queue)
    db.commit()
    db.refresh(queue)
    
    return {
        "status": "success",
        "message": "Аватарка загружена",
        "path": queue.q_img_path
    }

@app.get("/uploads/{filename}")
def get_uploaded_file(filename: str):
    """Получить загруженный файл"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    from fastapi.responses import FileResponse
    return FileResponse(file_path)



