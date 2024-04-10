from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from do_todo import setting
from typing import Annotated
from contextlib import asynccontextmanager 

class Todo(SQLModel, table=True):
    id : int = Field(default=None, primary_key=True)
    content : str = Field(index=True, min_length=1, max_length=255)
    is_complete : bool = Field(default=False)

connection_string : str = str(setting.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine =  create_engine(connection_string, connect_args={"sslmode": "require"}, pool_recycle=300, pool_size=10, echo=True)


def create_tables():
    SQLModel.metadata.create_all(engine)

# todo1 : Todo = Todo(content="First Todo")
# todo2 : Todo = Todo(content="Second Todo")

# session = Session(engine)

# session.add(todo1)
# session.add(todo2)
# print(f'Before Commit {todo1}')
# session.commit()
# session.refresh(todo1)
# print(f'After Commit {todo2}')
# session.close()

def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Creating Tables')
    create_tables()
    print('Tables Created')
    yield



app : FastAPI = FastAPI(lifespan=lifespan, title="Do Todo", version="0.1.0") 

@app.get("/")

async def root():
    return {"message": "Hello World"}

@app.post("/todos/", response_model=Todo)
async def create_todo(todo:Todo, session:Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

@app.get("/todos/", response_model=list[Todo])
async def get_all(session:Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    if todos:
        return todos
    else:
        raise HTTPException(status_code=404, detail="No Task found")


@app.get("/todos/{id}")
async def get_single_todo(id: int, session:Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if todo:
        return todo
    else:
        raise HTTPException(status_code=404, detail="No Task found")

@app.put("/todos/{id}")
async def edit_todo(id:int, todo:Todo, session:Annotated[Session, Depends(get_session)]):
    existing_todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_complete = todo.is_complete
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{id}")
async def delete_todo(id:int, session:Annotated[Session, Depends(get_session)]):
    todo = session.get(Todo, id)
    if todo:
        session.delete(todo)
        session.commit()
        return {"message": "Task successfuly deleted"}
    else:
        raise HTTPException(status_code=404, detail="Todo not found")