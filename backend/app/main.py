
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat  # import your chat router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Collaborative Writing Tool",
        description="Multi-agent writing with Autogen + Chroma + Azure.",
        version="1.0.0",
    )

    # ALLOW calls from localhost:3000 or 127.0.0.1:3000 (the Next.js frontend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include the chat router with prefix '/api/chat'
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

    # Root route so you don't get 404 at the base URL
    @app.get("/")
    def read_root():
        return {"detail": "Hello from FastAPI root!"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
