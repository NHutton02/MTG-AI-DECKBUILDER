from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="MTG AI Coach API")

class DeckRequest(BaseModel):
    format: str = "standard"
    seed: Optional[str] = None
    archetype: Optional[str] = None
    budget_usd: Optional[float] = None

class DeckResponse(BaseModel):
    mainboard: List[str]
    sideboard: List[str] = []
    explanation: str = ""

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/deck", response_model=DeckResponse)
def build_deck(req: DeckRequest):
    return DeckResponse(
        mainboard=["// TODO: implement builder"],
        explanation="This is a stub. Wire to engine.builder.build_deck(...)"
    )

class AskRequest(BaseModel):
    q: str

@app.post("/ask")
def ask(req: AskRequest):
    return {"answer": "Stub: the stack is a last-in, first-out zone where spells and abilities resolve."}
