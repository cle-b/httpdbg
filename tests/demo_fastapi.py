from typing import Union

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()


class Port(BaseModel):
    port: int


@app.get("/")
def hello_world():
    return "Hello, World!"


@app.get("/items/{item_id}")
def get_item(item_id: int, q: Union[str, None] = None):
    if item_id == 456:
        raise HTTPException(
            status_code=456,
            detail="custom exception",
            headers={"X-Error": "This is an HTTP 456 error"},
        )
    return {"item_id": item_id, "q": q}


@app.post("/withclientrequest")
def do_client_request(port: Port):
    requests.get(f"http://localhost:{port.port}/")
    return "ok"
