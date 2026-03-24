from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Привет!"}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return {"task_id": task_id, "name": f"Задача номер {task_id}"}