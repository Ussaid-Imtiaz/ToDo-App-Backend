from fastapi.testclient import TestClient
from fastapi import FastAPI, dependency_overrides
from do_todo import setting
from sqlmodel import create_engine, SQLModel, Session
from do_todo.main import app, get_session


connection_string : str = str(setting.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine =  create_engine(connection_string, connect_args={"sslmode": "require"}, pool_recycle=300, pool_size=10, echo=True)

def test_root():
    client = TestClient(app=app)
    response = client.get("/")
    data = response.json()
    assert response.status_code == 200
    assert data == {"message": "Hello World"}


def test_create_todo():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        def db_session_override():
            return session
    app.dependancy_overrides[get_session] = db_session_override
    client = TestClient(app=app)

    test_todo = {
        "content": "Test Todo",
        "completed": False
    }
    response = client.post("/todo/", json=test_todo)
    data = response.json()
    assert response.status_code == 200
    assert data["content"] == test_todo["content"]

