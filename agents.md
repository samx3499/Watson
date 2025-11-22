# Watson: RL-Trained LLM for Attack Detection via Multi-Hop Log Search

## Project Overview

This project aims to train a Large Language Model (LLM) to use **100s of tool calls** through **Reinforcement Learning (RL)**. The primary goal is to enable the agent to uncover attacks in heterogeneous logs via **long-horizon, multi-hop search** operations.

### Key Challenge
- **No dataset**: We don't have a pre-existing dataset
- **No verifiable rewards**: We need to generate rewards programmatically
- **Solution**: Use additional LLMs to:
  1. **Simulate the environment** (LLM pretending to be a database)
  2. **Calculate rewards** (LLM evaluating agent performance)

## Architecture

### Agent (Main LLM)
- **Output**: Human-readable search queries
- **Capability**: Long-horizon, multi-hop tool calls
- **Goal**: Uncover attack patterns in logs through iterative exploration

### Environment (Simulated DB LLM)
- **Role**: Pretends to be a database/log system
- **Input**: Human-readable search queries from the agent
- **Output**: Human-readable summaries of logs that would have been surfaced
- **Knowledge**: Has access to a specific attack scenario

### Example Interaction

```
Main Agent: "Run a query to group all logins by country and return the rarest ones"

Env Agent (knows attack scenario): "There are 3 countries. Australia: 272, New Zealand: 28, China: 1"
```

The environment LLM knows the attack scenario (e.g., suspicious login from China) and responds accordingly, simulating what a real database query would return.

## Attack Scenarios

We will develop **10-100 attack scenarios** covering various threat types:

- **Insider Threat**: Unauthorized access by internal users
- **Phishing Email**: Email-based attacks and credential harvesting
- **Ransomware**: Ransomware deployment and encryption activities
- **Data Exfiltration**: Unauthorized data transfers
- **Privilege Escalation**: Unauthorized privilege increases
- **Lateral Movement**: Network traversal by attackers
- *... (more scenarios to be defined)*

Each scenario will be embedded in the environment LLM, allowing the agent to discover attacks through systematic log analysis.

## Sim2Real Transfer

After training in the simulated environment, the system will translate between human-readable and machine-executable formats:

### Query Translation
- **Agent Output** → **DSL/KQL/SQL**: Convert human-readable queries to actual database query languages
- **Transparent to Agent**: The agent continues to work with human-readable queries

### Result Translation
- **Raw Database Rows** → **Human-Readable Summaries**: Convert query results back to summaries
- **Consistent Interface**: Agent experiences the same interface in both simulated and real environments

This bidirectional translation ensures the agent's training transfers seamlessly to real-world log analysis systems.

## Key Concepts

### 1. Reinforcement Learning (RL)
- Train the agent to optimize its search strategy
- Learn from rewards calculated by LLM-based reward model
- Explore long sequences of tool calls to maximize attack detection

### 2. Long-Horizon Multi-Hop Tool Calls
- Agent performs extended sequences of queries
- Each query builds on previous results
- Requires maintaining context across multiple steps
- Critical for uncovering complex attack patterns

### 3. LLM-Simulated Environment
- Flexible, scalable training without real infrastructure
- Can generate diverse scenarios and edge cases
- Allows rapid iteration and experimentation
- Environment LLM maintains attack scenario knowledge

### 4. Sim2Real Transfer
- Train in simulation, deploy to real systems
- Translation layer maintains interface consistency
- Agent remains agnostic to underlying query language
- Enables practical deployment after training

## Technical Stack

### Package Management
- **uv**: Fast Python package installer and resolver (https://github.com/astral-sh/uv)
  - Project uses `pyproject.toml` for dependency management
  - Run `uv sync` to install dependencies and create `uv.lock` file
  - Faster than pip and provides reproducible builds
  - The `uv.lock` file should be committed to version control for reproducibility

### Components
- **RL Framework**: PPO/DQN (Planned)
- **LLM Backend**: OpenRouter (OpenAI-compatible API) supporting GPT-4, Claude 3, etc.
- **Tool Call Framework**: Custom implementation with structured tool definitions
- **Environment**: LLM-simulated database with attack scenario knowledge
- **Evaluation**: Reward model LLM + WandB for experiment tracking
- **Data Collection**: OpenPipe SDK for logging and fine-tuning (Optional)

## Configuration

The project uses `dotenv` for configuration. Key environment variables:
- `OPENROUTER_API_KEY`: Required for LLM inference
- `WANDB_API_KEY`: Optional for experiment tracking
- `OPENPIPE_API_KEY`: Optional for cloud logging/fine-tuning

## Related Work

- **[ZeroSearch](https://alibaba-nlp.github.io/ZeroSearch/)**: Zero-shot tool-augmented reasoning for LLMs
  - Explores LLM capabilities for tool use without fine-tuning
  - Relevant for understanding tool call patterns and multi-hop reasoning

## Research Questions

1. How many tool calls can an agent effectively chain together?
2. What reward shaping strategies work best for multi-hop search?
3. How do we ensure the simulated environment accurately reflects real-world log patterns?
4. What's the optimal balance between exploration and exploitation in log analysis?
5. How do we handle false positives/negatives in attack detection?

## Implementation Phases

### Phase 1: Environment Simulation
- [x] Design attack scenario format
- [x] Implement environment LLM (simulated DB)
- [x] Create initial set of attack scenarios (6 scenarios implemented, target: 10-20)
- [x] Test environment responses

### Phase 2: Agent Development
- [x] Set up agent LLM with tool call capability
- [x] Implement query generation logic
- [x] Design context management for multi-hop queries
- [x] Create interaction loop between agent and environment

### Phase 3: Reward System
- [x] Design reward calculation LLM
- [x] Define reward metrics (attack detection, query efficiency, etc.)
- [x] Implement reward shaping strategies
- [x] Test reward signal quality

### Phase 4: RL Training
- [ ] Choose RL algorithm
- [ ] Set up training infrastructure
- [ ] Implement experience collection
- [ ] Train agent on attack scenarios

### Phase 5: Sim2Real Translation
- [ ] Build query translator (human-readable → DSL/KQL/SQL)
- [ ] Build result summarizer (raw rows → summaries)
- [ ] Test translation accuracy
- [ ] Validate agent performance on real systems

### Phase 6: Evaluation & Scaling
- [ ] Expand to 100 attack scenarios
- [ ] Evaluate on real log datasets
- [ ] Measure detection accuracy
- [ ] Optimize for production deployment

## Notes

- The agent should feel like it's interacting with a real database, even in simulation
- Translation layer must be bidirectional and lossless (or near-lossless)
- Reward model needs to balance attack detection with query efficiency
- Consider curriculum learning: start with simple scenarios, progress to complex ones

