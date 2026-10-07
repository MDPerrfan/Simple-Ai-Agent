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

class ChatRequest(BaseModel):
    message: str
    latitude: float | None = None
    longitude: float | None = None


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

        # Current-location search
        if (
            request.latitude is not None
            and request.longitude is not None
        ):
            from agent import search_nearby

            result = search_nearby(
                latitude=request.latitude,
                longitude=request.longitude
            )

        # Normal natural-language request
        else:
            result = restaurant_graph.invoke({
                "question": request.message
            })

        return {
            "answer": result["answer"]
        }

    except Exception:
        return {
            "error": "Unable to process your request right now."
        }