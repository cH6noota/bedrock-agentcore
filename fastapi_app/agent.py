import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
from strands import Agent
from strands.models import BedrockModel

app = FastAPI(title="Strands Agent Server", version="1.0.0")

MODEL_ID= os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
REGION_NAME = os.getenv("REGION_NAME", "us-east-1")

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION_NAME,
    temperature=0.3,
)
strands_agent = Agent(model=bedrock_model)


class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            raise HTTPException(
                status_code=400, 
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        result = strands_agent(user_message)
        response = {
            "message": result.message,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "strands-agent",
        }

        return InvocationResponse(output=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.get("/ping")
async def ping():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)