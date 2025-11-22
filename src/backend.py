import asyncio
import json
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# /workspaces/Watson/src/backend.py


app = FastAPI(title="Watson Agent API (Simulated)")

# In-memory stores (replace with persistent store in production)
INVESTIGATIONS: Dict[str, Dict[str, Any]] = {}
EVENT_QUEUES: Dict[str, asyncio.Queue] = {}

# Request model
class PromptRequest(BaseModel):
    prompt: str
    max_steps: Optional[int] = 8


async def _simulate_env_query(query: str) -> str:
    # Placeholder: simulate environment/db response
    await asyncio.sleep(0.2)
    return f"Simulated results for query: {query}"


async def _run_investigation_task(investigation_id: str, prompt: str, max_steps: int) -> None:
    """
    Background "agent" that performs a multi-hop investigation,
    emits events to a queue and writes a final report when finished.
    """
    q = EVENT_QUEUES[investigation_id]
    try:
        await q.put({"type": "started", "message": "Investigation started", "prompt": prompt})
        # initial parse
        await asyncio.sleep(0.1)
        await q.put({"type": "analysis", "message": "Parsing prompt and selecting first queries"})

        # Multi-hop simulated queries
        for step in range(1, max_steps + 1):
            query_text = f"Step {step}: generate query from prompt '{prompt[:80]}'"
            await q.put({"type": "query", "step": step, "query": query_text})
            # simulate environment response
            result = await _simulate_env_query(query_text)
            await q.put({"type": "result", "step": step, "result": result})

            # simple heuristic event
            if "suspicious" in result.lower() or step == max_steps:
                # mark a finding
                finding = {
                    "type": "finding",
                    "step": step,
                    "severity": "high" if step == max_steps else "medium",
                    "description": f"Simulated suspicious pattern discovered at step {step}",
                }
                await q.put(finding)

            await asyncio.sleep(0.1)

        # compose final report (in a real system this would be assembled from findings)
        final_report = {
            "investigation_id": investigation_id,
            "prompt": prompt,
            "summary": f"Simulated investigation completed with {max_steps} steps.",
            "findings": [
                {"id": "F-1", "description": "Suspicious login from rare country", "confidence": 0.92},
                {"id": "F-2", "description": "Unusual data transfer pattern", "confidence": 0.78},
            ],
        }
        # store report and emit final event
        INVESTIGATIONS[investigation_id]["report"] = final_report
        INVESTIGATIONS[investigation_id]["status"] = "completed"
        await q.put({"type": "final_report_ready", "report_summary": final_report["summary"]})
        await q.put({"type": "final_report", "report": final_report})
    except asyncio.CancelledError:
        await q.put({"type": "stopped", "message": "Investigation cancelled"})
        INVESTIGATIONS[investigation_id]["status"] = "cancelled"
    except Exception as e:
        await q.put({"type": "error", "error": str(e)})
        INVESTIGATIONS[investigation_id]["status"] = "error"
    finally:
        # mark finished for any consumers
        await q.put({"type": "stream_closed"})
        # Note: we keep queues & reports for retrieval; implement TTL/cleanup in production


@app.post("/investigate")
async def start_investigation(req: PromptRequest, background_tasks: BackgroundTasks):
    """
    Start an investigation given a human-readable prompt.
    Returns an investigation_id which can be used to stream events and fetch the final report.
    """
    investigation_id = str(uuid.uuid4())
    q: asyncio.Queue = asyncio.Queue()
    EVENT_QUEUES[investigation_id] = q
    INVESTIGATIONS[investigation_id] = {
        "prompt": req.prompt,
        "status": "running",
        "report": None,
    }
    # Kick off background task
    background_tasks.add_task(_run_investigation_task, investigation_id, req.prompt, req.max_steps or 8)
    return {"investigation_id": investigation_id, "status": "started"}


async def _event_generator(investigation_id: str) -> AsyncGenerator[bytes, None]:
    """
    Yields newline-delimited JSON events from the investigation queue.
    This implements a simple NDJSON streaming endpoint.
    """
    if investigation_id not in EVENT_QUEUES:
        raise HTTPException(status_code=404, detail="Investigation not found")

    q = EVENT_QUEUES[investigation_id]
    while True:
        event = await q.get()
        # The stream_closed marker signals the end of the stream, but we still yield it.
        yield (json.dumps(event) + "\n").encode("utf-8")
        if isinstance(event, dict) and event.get("type") == "stream_closed":
            break


@app.get("/events/{investigation_id}")
async def stream_events(investigation_id: str):
    """
    Stream a newline-delimited JSON (NDJSON) of events as the agent investigates.
    Clients should read the stream line-by-line and parse each line as JSON.
    """
    if investigation_id not in INVESTIGATIONS:
        raise HTTPException(status_code=404, detail="Investigation not found")

    # StreamingResponse will call the async generator to produce the response body
    return StreamingResponse(_event_generator(investigation_id), media_type="application/x-ndjson")


@app.get("/report/{investigation_id}")
async def get_report(investigation_id: str):
    """
    Fetch the final report of the investigation. If investigation is still running,
    returns the current status and any partial report when available.
    """
    meta = INVESTIGATIONS.get(investigation_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    status = meta.get("status")
    report = meta.get("report")
    return {"investigation_id": investigation_id, "status": status, "report": report}


if __name__ == "__main__":

    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)