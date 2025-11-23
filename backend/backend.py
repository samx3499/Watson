import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# /workspaces/Watson/src/backend.py


app = FastAPI(title="Watson Agent API (Simulated)")

# In-memory stores (replace with persistent store in production)
INVESTIGATIONS: Dict[str, Dict[str, Any]] = {}
EVENT_QUEUES: Dict[str, asyncio.Queue] = {}


# Request model
class PromptRequest(BaseModel):
    prompt: str
    max_steps: Optional[int] = 200


async def _simulate_env_query(query: str) -> str:
    # Placeholder: simulate environment/db response
    await asyncio.sleep(0.2)
    return f"Simulated results for query: {query}"


# --- Mocks moved from frontend ---
SCENARIOS = [
    {
        "id": "s1",
        "name": "APT29 Lateral Movement",
        "difficulty": "Hard",
        "description": "Simulates an adversary moving from a compromised edge node to the domain controller.",
    },
    {
        "id": "s2",
        "name": "Insider Data Exfiltration",
        "difficulty": "Medium",
        "description": "Detects unauthorized large file uploads by a privileged user during off-hours.",
    },
    {
        "id": "s3",
        "name": "Ransomware Deployment",
        "difficulty": "Hard",
        "description": "Identifies rapid file encryption patterns and shadow copy deletion commands.",
    },
    {
        "id": "phishing-credential-harvesting-001",
        "name": "Phishing Credential Harvesting via Malicious Website",
        "attack_type": "Phishing",
        "difficulty": 6,
        "date_discovered": "2024-03-16",
        "affected_system": "Windows 11 Enterprise (Build 22621)",
        "user": "sarah.mitchell@acmecorp.com",
        "workstation": "WS-ACME-0421",
        "description": "Phishing credential harvesting via spoofed corporate login page (acmecorp-security.com).",
    },
]

INITIAL_HOSTS = [
    {"id": "gw", "name": "Gateway-01", "type": "firewall", "status": "safe", "x": 50, "y": 100},
    {"id": "web", "name": "Web-FE-02", "type": "server", "status": "safe", "x": 200, "y": 50},
    {"id": "app", "name": "App-Svc-04", "type": "server", "status": "safe", "x": 200, "y": 150},
    {"id": "db", "name": "DB-PROD-01", "type": "database", "status": "safe", "x": 350, "y": 100},
    {"id": "ad", "name": "AD-Core", "type": "server", "status": "safe", "x": 500, "y": 100},
]

SIMULATION_SEQUENCE = [
    {
        "type": "thought",
        "content": "I need to investigate the initial alert regarding suspicious traffic from external IP 45.13.12.99.",
        "delay": 300,
    },
    {
        "type": "action",
        "content": "Search for inbound connections from 45.13.12.99.",
        "metadata": "Tool: Natural Language Query",
        "delay": 400,
    },
    {
        "type": "translation",
        "content": 'index=firewall src_ip="45.13.12.99" action="allowed" | stats count by dest_ip',
        "metadata": "Sim2Real: SQL/SPL Translator",
        "delay": 300,
    },
    {
        "type": "observation",
        "content": "Found connections to Gateway-01 on port 22 (SSH).",
        "delay": 300,
    },
    {
        "type": "reward",
        "content": "Initial Access Point Identified",
        "rewardValue": 5,
        "delay": 200,
    },
    # Explicit artifact describing the initial SSH access discovery
    {
        "type": "artifact",
        "description": "SSH access from 45.13.12.99 to Gateway-01 detected",
        "source": "Gateway-01",
        "impact": "Medium",
        "confidence": 0.45,
        "delay": 150,
    },
    {
        "type": "thought",
        "content": "Check for unusual outbound connections from Gateway-01.",
        "delay": 400,
    },
    {
        "type": "action",
        "content": "Query VPC flow logs for Gateway-01.",
        "metadata": "Tool: Natural Language Query",
        "delay": 300,
    },
    {
        "type": "translation",
        "content": 'index=vpc_flow src_ip="192.168.1.5" dest_port IN (1433, 5432, 3306)',
        "metadata": "Sim2Real: SQL/SPL Translator",
        "delay": 300,
    },
    {
        "type": "observation",
        "content": "Connection detected: Gateway-01 -> DB-PROD-01 (Port 1433). Bytes: 1.2GB",
        "delay": 300,
    },
    {
        "type": "reward",
        "content": "Suspicious outbound flow detected",
        "rewardValue": 10,
        "delay": 200,
    },
    # Artifact describing the suspicious outbound flow
    {
        "type": "artifact",
        "description": "Large outbound connection from Gateway-01 to DB-PROD-01 (1.2GB)",
        "source": "Gateway-01",
        "impact": "High",
        "confidence": 0.62,
        "delay": 150,
    },
    {
        "type": "action",
        "content": "Inspect DB sessions during the transfer window.",
        "metadata": "Tool: Natural Language Query",
        "delay": 300,
    },
    {
        "type": "translation",
        "content": 'index=wineventlog host="DB-PROD-01" EventCode=4624 | stats count by User',
        "metadata": "Sim2Real: SQL/SPL Translator",
        "delay": 300,
    },
    {
        "type": "observation",
        "content": 'User "svc_backup" active during anomalous transfer.',
        "delay": 300,
    },
    {"type": "reward", "content": "Credential misuse suspected", "rewardValue": 8, "delay": 200},
    {"type": "thought", "content": "Search for data staging artifacts.", "delay": 300},
    {
        "type": "action",
        "content": "List large file reads on DB-PROD-01.",
        "metadata": "Tool: Natural Language Query",
        "delay": 300,
    },
    {"type": "observation", "content": "Large read: /var/backups/backup.tar (2.0GB)", "delay": 300},
    {"type": "reward", "content": "Data staging confirmed", "rewardValue": 12, "delay": 200},
    # Artifact describing the data staging evidence
    {
        "type": "artifact",
        "description": "Large backup read /var/backups/backup.tar (2.0GB) on DB-PROD-01",
        "source": "DB-PROD-01",
        "impact": "High",
        "confidence": 0.7,
        "delay": 150,
    },
    {
        "type": "action",
        "content": "Check external transfer destinations.",
        "metadata": "Tool: Natural Language Query",
        "delay": 300,
    },
    {"type": "observation", "content": "External upload to 203.0.113.22 observed", "delay": 300},
    {"type": "reward", "content": "Exfiltration detected", "rewardValue": 20, "delay": 200},
    # Artifact describing the external upload observed
    {
        "type": "artifact",
        "description": "External upload to 203.0.113.22 observed",
        "source": "External-203.0.113.22",
        "impact": "Critical",
        "confidence": 0.9,
        "delay": 150,
    },
    {"type": "thought", "content": "Assemble final findings and confidence scores.", "delay": 300},
]

# Detailed phishing simulation sequence for scenario 'phishing-credential-harvesting-001'
PHISHING_SIMULATION_SEQUENCE = [
    {
        "type": "system",
        "content": "Investigation: Phishing Credential Harvesting detected for WS-ACME-0421",
        "delay": 100,
    },
    {
        "type": "thought",
        "content": "Network detections show outbound HTTPS to 185.220.101.45 (acmecorp-security.com).",
        "delay": 200,
    },
    {
        "type": "action",
        "content": "Query firewall and proxy logs for connections from WS-ACME-0421 to 185.220.101.45 and related domains.",
        "metadata": "Tool: Natural Language Query",
        "delay": 300,
    },
    {
        "type": "translation",
        "content": 'index=proxy src_ip="192.168.1.45" dest_ip="185.220.101.45" host=acmecorp-security.com | stats count by url',
        "metadata": "Sim2Real: SQL/SPL Translator",
        "delay": 200,
    },
    {
        "type": "observation",
        "content": "Outbound HTTPS observed: WS-ACME-0421 -> 185.220.101.45 (acmecorp-security.com). Cookies set and POST observed.",
        "delay": 200,
    },
    {
        "type": "reward",
        "content": "Suspicious domain contacted",
        "rewardValue": 6,
        "delay": 150,
    },
    {
        "type": "artifact",
        "description": "Edge History: Visit to https://acmecorp-security.com/verify-account (08:36:20 UTC)",
        "source": "WS-ACME-0421",
        "impact": "High",
        "confidence": 0.85,
        "delay": 150,
    },
    {
        "type": "artifact",
        "description": "Edge Cookies: session_id/tracking_id for acmecorp-security.com (created 08:36:20 UTC)",
        "source": "WS-ACME-0421",
        "impact": "High",
        "confidence": 0.88,
        "delay": 150,
    },
    {
        "type": "artifact",
        "description": "verify-account.lnk created pointing to https://acmecorp-security.com/verify-account (08:36:18 UTC)",
        "source": "WS-ACME-0421",
        "impact": "Medium",
        "confidence": 0.8,
        "delay": 120,
    },
    {
        "type": "observation",
        "content": "User input observed: credentials submitted to phishing page (POST to 185.220.101.45).",
        "delay": 200,
    },
    {
        "type": "reward",
        "content": "Credentials harvested",
        "rewardValue": 20,
        "delay": 100,
    },
    {
        "type": "artifact",
        "description": "Windows Event Log: msedge.exe started (Event ID 7034) and Application error (Event ID 1000) correlating with browser activity.",
        "source": "WS-ACME-0421",
        "impact": "Medium",
        "confidence": 0.65,
        "delay": 150,
    },
    {
        "type": "thought",
        "content": "Assemble timeline of browser artifacts, network connections, and cookie creation to confirm credential harvesting.",
        "delay": 250,
    },
    {
        "type": "observation",
        "content": "Timeline assembled: 08:36:18 - navigated, 08:36:20 - site loaded/cookies, 08:37:05 - creds entered, 08:37:06 - creds exfiltrated.",
        "delay": 200,
    },
    {
        "type": "reward",
        "content": "Phishing incident confirmed",
        "rewardValue": 12,
        "delay": 200,
    },
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
        await q.put(
            {
                "type": "system",
                "content": "Investigation started",
                "timestamp": int(asyncio.get_event_loop().time() * 1000),
            }
        )

        # Walk a selected simulation sequence and emit matching event types
        step_count = 0
        cumulative_reward = 0.0
        findings = []
        event_log = []
        # Select sequence based on the requested prompt; default to the generic sequence.
        sequence = SIMULATION_SEQUENCE
        try:
            lower_prompt = (prompt or "").lower()
        except Exception:
            lower_prompt = ""

        if "phishing-credential-harvesting-001" in (prompt or "") or "phishing" in lower_prompt:
            sequence = PHISHING_SIMULATION_SEQUENCE

        for item in sequence:
            # respect configured max_steps
            if step_count >= max_steps:
                break
            await asyncio.sleep(item.get("delay", 300) / 1000.0)
            step_count += 1

            # If the sequence item is an explicit artifact, construct and emit it
            if item.get("type") == "artifact":
                # Use provided fields if available, otherwise infer from content
                desc = str(item.get("description") or item.get("content") or "")
                src = item.get("source")
                impact = item.get("impact") or "Low"
                confidence = float(item.get("confidence") or 0.2)

                artifact_id = f"A-{investigation_id[:8]}-{len(findings) + 1}"
                artifact = {
                    "id": artifact_id,
                    "time": int(asyncio.get_event_loop().time() * 1000),
                    "type": "detection",
                    "description": desc,
                    "value": desc,
                    "impact": impact,
                    "confidence": round(min(0.99, confidence), 2),
                    "source": src,
                    "step": step_count,
                }
                findings.append(artifact)
                ev = {
                    "type": "artifact",
                    "artifact": artifact,
                    "timestamp": int(asyncio.get_event_loop().time() * 1000),
                }
                await q.put(ev)
                event_log.append(ev)
                # emit host status update if we can map the artifact source to a known host
                host_id = None
                host_name = artifact.get("source")
                for h in INITIAL_HOSTS:
                    if h.get("name") and host_name and h.get("name") in str(host_name):
                        host_id = h.get("id")
                        break

                status = "suspicious"
                if artifact.get("impact") in ("Critical", "High"):
                    status = "compromised"
                elif artifact.get("impact") == "Medium":
                    status = "suspicious"
                else:
                    status = "safe"

                host_ev = {
                    "type": "host_status",
                    "host_id": host_id,
                    "host_name": host_name,
                    "status": status,
                    "timestamp": int(asyncio.get_event_loop().time() * 1000),
                }
                await q.put(host_ev)
                event_log.append(host_ev)
                # skip emitting the generic event for artifact items
                continue

            # Build the generic event for non-artifact items
            event = {
                "type": item.get("type"),
                "content": item.get("content"),
                "timestamp": int(asyncio.get_event_loop().time() * 1000),
            }
            if item.get("metadata") is not None:
                event["metadata"] = item.get("metadata")

            # If the item carries a reward, attach values and also derive an artifact
            if item.get("rewardValue") is not None:
                # attach reward and cumulative reward values (signal-only)
                rv = float(item.get("rewardValue"))
                cumulative_reward += rv
                event["rewardValue"] = rv
                event["cumulativeReward"] = cumulative_reward

            # Emit the generic event (thought/action/observation/reward etc.)
            await q.put(event)
            event_log.append(event)

        # After sequence, assemble a final report
        final_report = {
            "investigation_id": investigation_id,
            "prompt": prompt,
            "summary": f"Simulated investigation completed with {step_count} steps.",
            "findings": [
                {
                    "id": "F-1",
                    "description": "Suspicious login from rare country",
                    "confidence": 0.92,
                },
                {"id": "F-2", "description": "Unusual data transfer pattern", "confidence": 0.78},
            ],
        }
        # include any dynamic findings discovered during run (artifacts)
        final_report["findings"] = findings if findings else final_report.get("findings", [])
        # include the sequence of emitted events so the UI can replay them
        # use a shallow copy to avoid circular references when we later emit the final_report event
        final_report["events"] = list(event_log)
        INVESTIGATIONS[investigation_id]["report"] = final_report
        INVESTIGATIONS[investigation_id]["status"] = "completed"

        # Emit final system and report events (they will not be included in final_report['events'] to avoid circular refs)
        ev1 = {
            "type": "system",
            "content": "Final report ready",
            "report_summary": final_report["summary"],
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
        }
        await q.put(ev1)
        # also append to the running event_log for external consumers if desired (kept separate from final_report.events)
        event_log.append(ev1)

        ev2 = {
            "type": "final_report",
            "report": final_report,
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
        }
        await q.put(ev2)
        event_log.append(ev2)
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
    # Kick off background task (default to larger step cap for richer simulations)
    background_tasks.add_task(
        _run_investigation_task, investigation_id, req.prompt, req.max_steps or 50
    )
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
