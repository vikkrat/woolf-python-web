"""Contact CRUD application with generated Swagger documentation."""

from fastapi import FastAPI
from app.contacts import router

app = FastAPI(title="Contacts API — homework 8", version="1.0.0")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
