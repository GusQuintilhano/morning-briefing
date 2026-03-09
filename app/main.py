from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from .database import engine, Base, get_db
from .routers import tasks, payments, briefing, push
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Morning Briefing", lifespan=lifespan)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(briefing.router, prefix="/api/briefing", tags=["briefing"])
app.include_router(push.router, prefix="/api/push", tags=["push"])

@app.get("/sw.js", response_class=FileResponse)
async def service_worker():
    sw_path = os.path.join(os.path.dirname(__file__), "templates", "sw.js")
    return FileResponse(sw_path, media_type="application/javascript")

API_KEY = os.getenv("API_KEY", "change-me-in-coolify")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db=Depends(get_db)):
    from .routers.tasks import get_tasks_db
    from .routers.payments import get_payments_db
    from .routers.briefing import get_latest_briefing

    tasks_list = get_tasks_db(db)
    payments_list = get_payments_db(db)
    briefing_data = get_latest_briefing(db)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "tasks": tasks_list,
        "payments": payments_list,
        "briefing": briefing_data,
    })

@app.get("/health")
async def health():
    return {"status": "ok"}
