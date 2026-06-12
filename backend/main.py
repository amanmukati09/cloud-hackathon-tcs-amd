from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from routers import diagnosis, incidents, chat, community, admin, notifications

app = FastAPI(title="AegisAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(diagnosis.router)
app.include_router(incidents.router)
app.include_router(chat.router)
app.include_router(community.router)
app.include_router(admin.router)
app.include_router(notifications.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)