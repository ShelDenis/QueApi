from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date, datetime, timedelta
from models import Queue, User, ChatMessage
from schemas import QueueCreate

def update_activity(db: Session, queue: Queue):
    #Обновляет время последней активности
    queue.last_activity = datetime.now()
    db.add(queue)
    db.commit()

def create_queue(db: Session, queue_data: QueueCreate, creator_id: int):
    user = db.execute(select(User).where(User.u_id == creator_id)).scalar_one_or_none()
    if not user:
        raise ValueError("Пользователь не найден")
    
    new_queue = Queue(
        q_name=queue_data.q_name,
        q_describe=queue_data.q_describe,
        q_img_path=queue_data.q_img_path,
        q_creation_date=date.today(),
        q_creator_id=creator_id,
        q_sequence=[],
        last_activity=datetime.now()  # Устанавливаем время создания
    )
    
    db.add(new_queue)
    db.commit()
    db.refresh(new_queue)
    return new_queue

def add_to_queue(db: Session, queue_id: int, user_id: int):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise ValueError("Очередь не найдена")
    
    user = db.execute(select(User).where(User.u_id == user_id)).scalar_one_or_none()
    if not user:
        raise ValueError("Пользователь не найден")
    
    current_sequence = queue.q_sequence if queue.q_sequence else []
    
    if user_id in current_sequence:
        raise ValueError("Пользователь уже в очереди")
    
    new_sequence = current_sequence + [user_id]
    queue.q_sequence = new_sequence
    queue.last_activity = datetime.now()  # Обновляем активность
    
    db.add(queue)
    db.commit()
    db.refresh(queue)
    
    return {
        "status": "success",
        "position": len(queue.q_sequence),
        "queue_id": queue_id,
        "user_id": user_id,
        "participants_count": len(queue.q_sequence)
    }

def leave_queue(db: Session, queue_id: int, user_id: int):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise ValueError("Очередь не найдена")
    
    current_sequence = queue.q_sequence if queue.q_sequence else []
    
    if user_id not in current_sequence:
        raise ValueError("Пользователь не в очереди")
    
    new_sequence = [uid for uid in current_sequence if uid != user_id]
    queue.q_sequence = new_sequence
    queue.last_activity = datetime.now()  # Обновляем активность
    
    db.add(queue)
    db.commit()
    db.refresh(queue)
    
    return {
        "status": "success",
        "message": "Вы вышли из очереди",
        "queue_id": queue_id,
        "user_id": user_id,
        "participants_count": len(queue.q_sequence)
    }

def rejoin_queue(db: Session, queue_id: int, user_id: int):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise ValueError("Очередь не найдена")
    
    current_sequence = queue.q_sequence if queue.q_sequence else []
    
    if user_id not in current_sequence:
        raise ValueError("Пользователь не в очереди")
    
    without_user = [uid for uid in current_sequence if uid != user_id]
    new_sequence = without_user + [user_id]
    queue.q_sequence = new_sequence
    queue.last_activity = datetime.now()  # Обновляем активность
    
    db.add(queue)
    db.commit()
    db.refresh(queue)
    
    return {
        "status": "success",
        "message": "Перемещены в конец",
        "new_position": len(queue.q_sequence),
        "participants_count": len(queue.q_sequence)
    }

def send_message(db: Session, queue_id: int, user_id: int, text: str):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise ValueError("Очередь не найдена")
    
    participants = queue.q_sequence if queue.q_sequence else []
    
    if user_id not in participants and queue.q_creator_id != user_id:
        raise ValueError("Вы не состоите в этой очереди")
    
    # Обновляем активность очереди
    queue.last_activity = datetime.now()
    db.add(queue)
    
    now = datetime.now()
    new_message = ChatMessage(
        q_id=queue_id,
        u_id=user_id,
        m_text=text,
        m_date=now.date(),
        m_time=now.time()
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return new_message

def get_queue_messages(db: Session, queue_id: int, user_id: int):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        raise ValueError("Очередь не найдена")
    
    participants = queue.q_sequence if queue.q_sequence else []
    if user_id not in participants and queue.q_creator_id != user_id:
        raise ValueError("Вы не состоите в этой очереди")
    
    messages = db.execute(
        select(ChatMessage)
        .where(ChatMessage.q_id == queue_id)
        .order_by(ChatMessage.m_date, ChatMessage.m_time)
    ).scalars().all()
    
    result = []
    for msg in messages:
        user = db.execute(select(User).where(User.u_id == msg.u_id)).scalar_one()
        result.append({
            "m_id": msg.m_id,
            "user_name": f"{user.u_name} {user.u_surname}",
            "user_id": msg.u_id,
            "text": msg.m_text,
            "date": str(msg.m_date),
            "time": str(msg.m_time)
        })
    return result

def get_queue_by_id(db: Session, queue_id: int):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if not queue:
        return None
    
    return {
        "q_id": queue.q_id,
        "q_name": queue.q_name,
        "q_describe": queue.q_describe,
        "participants_count": len(queue.q_sequence) if queue.q_sequence else 0,
        "participants": queue.q_sequence if queue.q_sequence else [],
        "last_activity": queue.last_activity.isoformat() if queue.last_activity else None
    }

def delete_queue(db: Session, queue_id: int):
    queue = db.execute(select(Queue).where(Queue.q_id == queue_id)).scalar_one_or_none()
    if queue:
        db.delete(queue)
        db.commit()
        return True
    return False

def cleanup_empty_queues(db: Session):
    ten_minutes_ago = datetime.now() - timedelta(minutes=10)
    
    queues_to_delete = db.execute(
        select(Queue).where(
            Queue.last_activity < ten_minutes_ago,
            Queue.q_sequence == []  # Пустая очередь
        )
    ).scalars().all()
    
    deleted_count = 0
    for queue in queues_to_delete:
        db.delete(queue)
        deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
    
    return deleted_count