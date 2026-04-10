from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from models import Queue, User
from schemas import QueueCreate

async def create_queue(
    db: AsyncSession,
    queue_data: QueueCreate,
    creator_id: int
):
    result = await db.execute(select(User).where(User.u_id == creator_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("Пользователь не найден")
    
    new_queue = Queue(
        q_name=queue_data.q_name,
        q_describe=queue_data.q_describe,
        q_img_path=queue_data.q_img_path,
        q_creation_date=date.today(),
        q_creator_id=creator_id,
        q_sequence=[]  # Пустой список участников
    )
    
    db.add(new_queue)
    await db.flush()
    await db.refresh(new_queue)
    
    return new_queue


async def add_to_queue(
    db: AsyncSession,
    queue_id: int,
    user_id: int
):
    # Получаем очередь
    result = await db.execute(select(Queue).where(Queue.q_id == queue_id))
    queue = result.scalar_one_or_none()
    
    if not queue:
        raise ValueError("Очередь не найдена")
    
    # Проверяем, не в очереди ли уже
    if user_id in queue.q_sequence:
        raise ValueError("Пользователь уже в очереди")
    
    # Добавляем в конец
    queue.q_sequence.append(user_id)
    
    await db.flush()
    await db.refresh(queue)
    
    return {"position": len(queue.q_sequence), "queue": queue.q_sequence}


async def leave_queue(
    db: AsyncSession,
    queue_id: int,
    user_id: int
):
    result = await db.execute(select(Queue).where(Queue.q_id == queue_id))
    queue = result.scalar_one_or_none()
    
    if not queue:
        raise ValueError("Очередь не найдена")
    
    if user_id not in queue.q_sequence:
        raise ValueError("Пользователь не в очереди")
    
    # Удаляем пользователя
    queue.q_sequence.remove(user_id)
    
    await db.flush()
    await db.refresh(queue)
    
    return {"message": "Вы вышли из очереди", "queue": queue.q_sequence}


async def rejoin_queue(
    db: AsyncSession,
    queue_id: int,
    user_id: int
):
    result = await db.execute(select(Queue).where(Queue.q_id == queue_id))
    queue = result.scalar_one_or_none()
    
    if not queue:
        raise ValueError("Очередь не найдена")
    
    if user_id not in queue.q_sequence:
        raise ValueError("Пользователь не в очереди")
    
    # Удаляем с текущей позиции
    queue.q_sequence.remove(user_id)
    # Добавляем в конец
    queue.q_sequence.append(user_id)
    
    await db.flush()
    await db.refresh(queue)
    
    return {"message": "Перемещены в конец", "new_position": len(queue.q_sequence)}


async def send_message(
    db: AsyncSession,
    queue_id: int,
    user_id: int,
    text: str
):
    from models import ChatMessage
    from datetime import datetime
    
    # Проверяем очередь
    queue_result = await db.execute(select(Queue).where(Queue.q_id == queue_id))
    if not queue_result.scalar_one_or_none():
        raise ValueError("Очередь не найдена")
    
    # Проверяем пользователя
    user_result = await db.execute(select(User).where(User.u_id == user_id))
    if not user_result.scalar_one_or_none():
        raise ValueError("Пользователь не найден")
    
    now = datetime.now()
    new_message = ChatMessage(
        q_id=queue_id,
        u_id=user_id,
        m_text=text,
        m_date=now.date(),
        m_time=now.time()
    )
    
    db.add(new_message)
    await db.flush()
    await db.refresh(new_message)
    
    return new_message