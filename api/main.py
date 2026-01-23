from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from settings import get_settings
from apscheduler.schedulers.background import BackgroundScheduler

from routers import auth, api_user, product
from tasks.cleanup import cleanup_expired_refresh_tokens


settings = get_settings()


scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_expired_refresh_tokens, "interval", hours=24)  # every 6h




@asynccontextmanager
async def lifespan(app: FastAPI):

    if settings.SCHEDULER_ACTIVE:
        scheduler.start()
    yield  # app runs during this period
    scheduler.shutdown()  # cleanly stop on shutdown


app = FastAPI(
    title="SAP Backend",
    docs_url="/docs" if settings.SWAGGER_ACTIVE else None,
    redoc_url=None,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN],  # The default React port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(api_user.router)
app.include_router(product.router)
