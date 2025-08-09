from contextlib import asynccontextmanager

from aiohttp import ClientSession as AsyncHttpSession
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import src.function.scheduled
from src.function.views import router as function_router

from .config import config
from .scheduler import scheduler

k8s_client = config.get_k8s_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load APScheduler
    scheduler.start()
    app.state.http_session = AsyncHttpSession()
    yield
    # Cleanup APScheduler
    scheduler.shutdown()
    await app.state.http_session.close()


app = FastAPI(root_path="/api", lifespan=lifespan)

# Jobs in queue
scheduler.print_jobs()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(function_router, prefix="/functions")

# The SPA frontend files must be the last thing in the routing, it'll match any path.
app.mount("/", StaticFiles(directory="src/static/dist", html=True))
