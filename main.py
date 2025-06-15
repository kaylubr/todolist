from database import engine, SessionLocal
from fastapi import FastAPI, Depends, Path, HTTPException
from models import Todos
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
import models


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class TodoRequest(BaseModel):
    title: Annotated[str, Field(min_length=3)]
    description: Annotated[str, Field(min_length=1, max_length=100)]
    priority: Annotated[int, Field(ge=1, le=5)]
    complete: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Go study for finals",
                "description": "I've gotta pass all of my tests.",
                "priority": 5,
                "complete": False,
            }
        }
    }


# Get all todo
@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Todos).all()


# Get specific todo
@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo(db: db_dependency, todo_id: Annotated[int, Path(ge=1)]):
    todo_obj = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_obj:
        return todo_obj

    raise HTTPException(status_code=404, detail="Resource not found.")


# Create todo
@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, request_body: TodoRequest):
    todo_obj = Todos(**request_body.model_dump())
    db.add(todo_obj)
    db.commit()


@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    db: db_dependency, todo_id: Annotated[int, Path(ge=1)], request_body: TodoRequest
):
    todo_obj = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_obj is None:
        raise HTTPException(status_code=404, detail="Resource not found.")

    todo_obj.title = request_body.title
    todo_obj.description = request_body.description
    todo_obj.priority = request_body.priority
    todo_obj.complete = request_body.complete

    db.add(todo_obj)
    db.commit()


@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: Annotated[int, Path(ge=1)]):
    todo_obj = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_obj is None:
        raise HTTPException(status_code=404, detail="Resource not found.")

    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
