"""FastAPI application assembly and CORS configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import auth, contacts, users
from app.config import settings

app = FastAPI(title="Contacts API — final homework", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(users.router)


@app.get("/health", tags=["health"])
def health():
    """Return the API liveness status."""
    return {"status": "ok"}
