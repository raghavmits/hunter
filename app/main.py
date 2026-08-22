from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import companies, contacts

app = FastAPI(title="Hunter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router)
app.include_router(companies.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
