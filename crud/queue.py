from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from models import Queue, User  
from schemas import QueueCreate  
from datetime import date, datetime  
from models import ChatMessage      

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
        q_sequence=[]
    )
    
    db.add(new_queue)
    await db.flush()
    await db.refresh(new_queue)
    
    return new_queue



from models import QueueMember 

async def add_to_queue(
    db: AsyncSession,
    queue_id: int,
    user_id: int
):
    # Проверяем, существует ли очередь
    result = await db.execute(select(Queue).where(Queue.q_id == queue_id))
    queue = result.scalar_one_or_none()
    
    if not queue:
        raise ValueError("Очередь не найдена")
    
    # Проверяем, не в очереди ли уже пользователь
    existing = await db.execute(
        select(QueueMember).where(
            QueueMember.queue_id == queue_id,
            QueueMember.user_id == user_id
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Пользователь уже в очереди")
    
    # Определяем позицию в конец
    last_position = await db.execute(
        select(QueueMember).where(QueueMember.queue_id == queue_id)
    )
    position = len(last_position.all()) + 1
    
    # Добавляем в очередь
    new_member = QueueMember(
        queue_id=queue_id,
        user_id=user_id,
        position=position,
        status="waiting"
    )
    
    db.add(new_member)
    await db.flush()
    await db.refresh(new_member)
    
    return new_member




async def leave_queue(
    db: AsyncSession,
    queue_id: int,
    user_id: int
):
    # Находим участника
    result = await db.execute(
        select(QueueMember).where(
            QueueMember.queue_id == queue_id,
            QueueMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise ValueError("Пользователь не находится в этой очереди")
    
    # Запоминаем позицию удаляемого
    old_position = member.position
    
    # Удаляем участника
    await db.delete(member)
    await db.flush()
    
    # Сдвигаем позиции у тех, кто был после него
    await db.execute(
        select(QueueMember).where(
            QueueMember.queue_id == queue_id,
            QueueMember.position > old_position
        )
    )
    remaining = result.scalars().all()
    
    for m in remaining:
        m.position -= 1
    
    await db.flush()
    
    return {"message": "Вы вышли из очереди", "old_position": old_position}


async def rejoin_queue(
    db: AsyncSession,
    queue_id: int,
    user_id: int
):
    # Находим участника
    result = await db.execute(
        select(QueueMember).where(
            QueueMember.queue_id == queue_id,
            QueueMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise ValueError("Пользователь не находится в этой очереди")
    
    # Запоминаем старую позицию
    old_position = member.position
    
    # Находим максимальную позицию
    max_pos_result = await db.execute(
        select(QueueMember).where(QueueMember.queue_id == queue_id)
    )
    members = max_pos_result.scalars().all()
    max_position = max([m.position for m in members]) if members else 0
    
    # Сдвигаем всех, кто был после old_position
    for m in members:
        if m.position > old_position:
            m.position -= 1
    
    # Перемещаем пользователя в конец
    member.position = max_position
    
    await db.flush()
    await db.refresh(member)
    
    return {"message": "Вы перемещены в конец очереди", "new_position": member.position}




async def send_message(
    db: AsyncSession,
    queue_id: int,
    user_id: int,
    text: str
):
    # Проверяем существование очереди
    queue_result = await db.execute(select(Queue).where(Queue.q_id == queue_id))
    if not queue_result.scalar_one_or_none():
        raise ValueError("Очередь не найдена")
    
    # Проверяем существование пользователя
    user_result = await db.execute(select(User).where(User.u_id == user_id))
    if not user_result.scalar_one_or_none():
        raise ValueError("Пользователь не найден")
    
    # Создаем сообщение
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