from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db  
from schemas import QueueCreate, QueueResponse  
from crud.queue import create_queue  
from schemas import JoinQueueRequest  
from crud.queue import add_to_queue   
from crud.queue import create_queue, add_to_queue, leave_queue
from crud.queue import create_queue, add_to_queue, leave_queue, rejoin_queue 
from schemas import MessageCreate, MessageResponse  
from crud.queue import send_message                 

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Привет!"}

@app.post("/queues", response_model=QueueResponse)
async def create_queue_endpoint(
    queue_data: QueueCreate,
    creator_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        new_queue = await create_queue(db, queue_data, creator_id)
        return new_queue
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    




@app.post("/queues/{queue_id}/join")
async def join_queue(
    queue_id: int,
    request: JoinQueueRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await add_to_queue(db, queue_id, request.user_id)
        return {"message": "Вы добавлены в очередь", "position": result.position}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/queues/{queue_id}/leave")
async def leave_queue(
    queue_id: int,
    request: JoinQueueRequest,  # переиспользуем ту же схему с user_id
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await leave_queue(db, queue_id, request.user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    




@app.post("/queues/{queue_id}/rejoin")
async def rejoin_queue_endpoint(
    queue_id: int,
    request: JoinQueueRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await rejoin_queue(db, queue_id, request.user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/messages", response_model=MessageResponse)
async def send_message_endpoint(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await send_message(db, message.queue_id, message.user_id, message.text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))