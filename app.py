import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from agent.orchestrator import Orchestrator

app = FastAPI(
    title="AegisBox | Blast Radius Zero Agent",
    description="Containment-first autonomous agent runner deployed on Vultr infrastructure",
    version="1.0.0"
)

orchestrator = Orchestrator()

class ExecutionRequest(BaseModel):
    goal: str
    code: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def index():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/api/execute")
async def execute_task(req: ExecutionRequest):
    result = await orchestrator.execute_task(user_goal=req.goal, override_code=req.code)
    return result

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AegisBox",
        "challenge": "Blast Radius Zero",
        "infrastructure": {
            "platform": "Vultr Cloud Compute",
            "inference": "Vultr Serverless Inference (api.vultrinference.com/v1)",
            "containment_mode": "Strict Zero-Blast"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
