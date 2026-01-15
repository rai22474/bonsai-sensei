from fastapi import APIRouter, Request
from bonsai_sensei.telegram import bot

router = APIRouter()

@router.get("/")
def read_root():
    return {"Hello": "World"}
