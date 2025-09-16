from fastapi import FastAPI
from app.routes import codes, contexts, establishments

app = FastAPI()

# Register routers
app.include_router(codes.router)
app.include_router(contexts.router)
app.include_router(establishments.router)

@app.get("/")
def root():
    return {"message": "API is running"}
