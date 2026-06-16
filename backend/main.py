from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from auth import router as auth_router
from routers import diagnosis, incidents, chat, community, admin, notifications, workflow, audit, workspace, api_keys, workers
from middleware.rate_limit import RateLimitMiddleware
from workers.tasks import start_worker, stop_worker
from routers import dashboard
from routers import timeline
from routers import bulk_pdf
from routers import train
from routers import dependency
from routers import sql_runner
from routers import analytics
from routers import live_monitor
from routers import rl_triage



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_worker()
    yield
    # Shutdown
    stop_worker()

app = FastAPI(title="AegisAI Backend", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Include routers
app.include_router(auth_router)
app.include_router(diagnosis.router)
app.include_router(incidents.router)
app.include_router(chat.router)
app.include_router(community.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(workflow.router)
app.include_router(audit.router)
app.include_router(workspace.router)
app.include_router(api_keys.router)
app.include_router(workers.router)
app.include_router(dashboard.router)
app.include_router(timeline.router)
app.include_router(bulk_pdf.router)
app.include_router(train.router)
app.include_router(dependency.router)
app.include_router(analytics.router)
app.include_router(live_monitor.router)
app.include_router(sql_runner.router)
app.include_router(rl_triage.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)