from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from agent import restaurant_graph


app = FastAPI(
    title="AI Dining Assistant API"
)


# Allow React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Expected request format
class ChatRequest(BaseModel):
    message: str


# Simple health check
@app.get("/")
def home():
    return {
        "status": "running",
        "message": "AI Dining Assistant API"
    }


# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):

    try:
        result = restaurant_graph.invoke({
            "question": request.message
        })

        return {
            "answer": result["answer"]
        }

    except Exception as e:
        return {
            "error": str(e)
        }