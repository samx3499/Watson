import asyncio
import json
import uuid
import os
import re
from typing import Any, AsyncGenerator, Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
     