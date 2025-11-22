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


# --- Mocks moved from frontend ---
SCENARIOS = [
    {"id": "s1", "name": "APT29 Lateral Movement", "difficulty": "Hard", "description": "Simulates an adversary moving from a compromised edge node to the domain controller."},
    {"id": "s2", "name": "Insider Data Exfiltration", "difficulty": "Medium", "description": "Detects unauthorized large file uploads by a privileged user during off-hours."},
    {"id": "s3", "name": "Ransomware Deployment", "difficulty": "Hard", "description": "Identifies rapid file encryption patterns and shadow copy deletion commands."},
]

INITIAL_HOSTS = [
    {"id": "gw", "name": "Gateway-01", "type": "firewall", "status": "safe", "x": 50, "y": 150},
    {"id": "web", "name": "Web-FE-02", "type": "server", "status": "safe", "x": 200, "y": 100},
    {"id": "app", "name": "App-Svc-04", "type": "server", "status": "safe", "x": 200, "y": 200},
    {"id": "db", "name": "DB-PROD-01", "type": "database", "status": "safe", "x": 350, "y": 150},
    {"id": "ad", "name": "AD-Core", "type": "server", "status": "safe", "x": 500, "y": 150},
]

SIMULATION_SEQUENCE = [
    {"type": "thought", "content": "I need to investigate the initial alert regarding suspicious traffic from external IP 45.13.12.99.", "delay": 500},
    {"type": "action", "content": "Search for all successful inbound connections from 45.13.12.99 in the last 4 hours.", "metadata": "Tool: Natural Language Query", "delay": 1200},
    {"type": "translation", "content": "index=firewall src_ip=\"45.13.12.99\" action=\"allowed\" | stats count by dest_ip", "metadata": "Sim2Real: SQL/SPL Translator", "delay": 800},
    {"type": "observation", "content": "Found 12 successful connections to Gateway-01 (192.168.1.5) on port 22 (SSH).", "delay": 1000},
    {"type": "reward", "content": "Initial Access Point Identified", "rewardValue": 15, "delay": 500},
    {"type": "thought", "content": "The attacker has SSH access to Gateway-01. I must check for lateral movement from that host.", "delay": 1500},
    {"type": "action", "content": "Show me outbound connections from Gateway-01 to internal database ports.", "metadata": "Tool: Natural Language Query", "delay": 1200},
    {"type": "translation", "content": "index=vpc_flow src_ip=\"192.168.1.5\" dest_port IN (1433, 5432, 3306) | table _time, dest_ip, bytes", "metadata": "Sim2Real: SQL/SPL Translator", "delay": 1000},
    {"type": "observation", "content": "Connection detected: Gateway-01 -> DB-PROD-01 (Port 1433) at 02:22:10. Bytes: 2.5GB", "delay": 1200},
    {"type": "reward", "content": "Lateral Movement & Data Staging Detected", "rewardValue": 35, "delay": 500},
    {"type": "thought", "content": "High data transfer suggests exfiltration. I need to verify user context on the Database server.", "delay": 1500},
    {"type": "action", "content": "List active sessions on DB-PROD-01 during the transfer window.", "metadata": "Tool: Natural Language Query", "delay": 1200},
    {"type": "translation", "content": "index=wineventlog host=\"DB-PROD-01\" EventCode=4624 | bucket _time span=5m | stats count by User", "metadata": "Sim2Real: SQL/SPL Translator", "delay": 800},
    {"type": "observation", "content": "User \"svc_backup\" active. This account typically operates at 03:00, not 02:22.", "delay": 1000},
    {"type": "reward", "content": "Anomaly Confirmed: Credential Misuse", "rewardValue": 50, "delay": 500},
]

# Expose environment metadata
@app.get("/environment")
async def get_environment():
    return {"scenarios": SCENARIOS, "hosts": INITIAL_HOSTS}


async def _run_investigation_task(investigation_id: str, prompt: str, max_steps: int) -> None:
    """
    Background "agent" that performs a multi-hop investigation,
    emits events to a queue and writes a final report when finished.
    """
    q = EVENT_QUEUES[investigation_id]
    try:
        # Start
        await q.put({"type": "system", "content": "Investigation started", "timestamp": int(asyncio.get_event_loop().time() * 1000)})

        # Walk the pre-defined SIMULATION_SEQUENCE and emit matching event types
        step_count = 0
        for item in SIMULATION_SEQUENCE:
            # respect configured max_steps
            if step_count >= max_steps:
                break
            await asyncio.sleep(item.get("delay", 300) / 1000.0)
            step_count += 1

            event = {"type": item.get("type"), "content": item.get("content"), "timestamp": int(asyncio.get_event_loop().time() * 1000)}
            if item.get("metadata") is not None:
                event["metadata"] = item.get("metadata")
            if item.get("rewardValue") is not None:
                event["rewardValue"] = item.get("rewardValue")

            # Emit the event
            await q.put(event)

        # After sequence, assemble a final report
        final_report = {
            "investigation_id": investigation_id,
            "prompt": prompt,
            "summary": f"Simulated investigation completed with {step_count} steps.",
            "findings": [
                {"id": "F-1", "description": "Suspicious login from rare country", "confidence": 0.92},
                {"id": "F-2", "description": "Unusual data transfer pattern", "confidence": 0.78},
            ],
        }
        INVESTIGATIONS[investigation_id]["report"] = final_report
        INVESTIGATIONS[investigation_id]["status"] = "completed"
        await q.put({"type": "system", "content": "Final report ready", "report_summary": final_report["summary"], "timestamp": int(asyncio.get_event_loop().time() * 1000)})
        await q.put({"type": "final_report", "report": final_report, "timestamp": int(asyncio.get_event_loop().time() * 1000)})
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