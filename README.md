# Watson: RL-Trained LLM for Attack Detection via Multi-Hop Log Search

This project trains a Large Language Model (LLM) to use **100s of tool calls** through **Reinforcement Learning (RL)**. The primary goal is to enable the agent to uncover attacks in heterogeneous logs via **long-horizon, multi-hop search** operations.

## Architecture

### Components

1. **Agent LLM**: The main agent that performs multi-hop log searches using tool calls
2. **Environment LLM**: Simulates a database/log system that responds to queries
3. **Reward LLM**: Evaluates agent performance and calculates rewards
4. **OpenPipe Integration**: Collects training data and manages fine-tuning

### How It Works

1. **Episode Execution**: The agent investigates an attack scenario by making multiple queries to the environment
2. **Data Collection**: All interactions are logged to OpenPipe using the SDK
3. **Reward Calculation**: The reward LLM evaluates how well the agent discovered the attack
4. **Fine-Tuning**: Collected data is used to create datasets and fine-tune models

## Setup

### Prerequisites

- Python 3.8+
- OpenRouter API key (get from https://openrouter.ai/keys)
- WandB API key (optional, for experiment tracking - get from https://wandb.ai/settings)
- OpenPipe API key (optional, only needed for cloud logging/fine-tuning - get from https://app.openpipe.ai/settings)

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Install dependencies using uv**:
   ```bash
   # Install uv if you haven't already: https://github.com/astral-sh/uv
   uv sync
   ```
   
   This will install all dependencies and create a `uv.lock` file for reproducible builds.
   
   Alternatively, you can use pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   
   Create a `.env` file in the project root:
   ```bash
   # OpenRouter API Key (required - get from https://openrouter.ai/keys)
   OPENROUTER_API_KEY=sk-or-v1-...
   
   # WandB API Key (optional - for experiment tracking)
   WANDB_API_KEY=your-wandb-key
   WANDB_PROJECT=watson  # Optional: WandB project name
   
   # OpenPipe API Key (optional - only needed for cloud logging/fine-tuning)
   # OPENPIPE_API_KEY=opk-...
   
   # Optional: Model configurations (OpenRouter model names)
   AGENT_MODEL=openai/gpt-4
   ENVIRONMENT_MODEL=openai/gpt-4
   REWARD_MODEL=openai/gpt-4
   ```
   
   **Note**: OpenRouter is OpenAI-compatible, so you can use any model available on OpenRouter. 
   See https://openrouter.ai/models for available models.

## Usage

### 1. Collect Training Data

Run episodes to collect training data. All interactions are automatically logged to OpenPipe.

```bash
# Run all scenarios (1 episode each)
python scripts/collect_data.py

# Run specific scenarios
python scripts/collect_data.py --scenarios insider-threat-001 phishing-001

# Run multiple episodes per scenario
python scripts/collect_data.py --episodes-per-scenario 5

# Run only easy scenarios (difficulty <= 5)
python scripts/collect_data.py --max-difficulty 5
```

Episode results are saved to `data/episodes/` directory.

### 2. Create Dataset in OpenPipe

After collecting episodes, create a dataset and add the training data:

```bash
# Create a new dataset
python scripts/manage_datasets.py create-dataset --name "watson-agent-training-v1"

# Add episodes to the dataset (replace DATASET_ID with the ID from previous command)
python scripts/manage_datasets.py add-entries \
    --dataset-id DATASET_ID \
    --episodes-dir data/episodes
```

### 3. Create Fine-Tune Job

Once your dataset has entries, create a fine-tune job:

```bash
python scripts/manage_datasets.py create-finetune \
    --dataset-id DATASET_ID \
    --slug watson-agent-v1 \
    --base-model meta-llama/Llama-2-13b-hf
```

### 4. Check Fine-Tune Status

Monitor your fine-tune job:

```bash
python scripts/manage_datasets.py finetune-status --finetune-id FINETUNE_ID
```

## Project Structure

```
Watson/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── scenarios.py            # Attack scenario definitions
│   ├── agent.py                # Main agent LLM
│   ├── environment.py         # Environment LLM (simulated DB)
│   ├── reward.py               # Reward calculation LLM
│   └── episode.py              # Episode runner
├── scripts/
│   ├── collect_data.py         # Data collection script
│   └── manage_datasets.py      # OpenPipe dataset/finetune management
├── data/
│   └── episodes/               # Episode results (created at runtime)
├── requirements.txt
├── agents.md                   # Project overview and research plan
└── README.md                   # This file
```

## Attack Scenarios

The project includes several pre-defined attack scenarios:

- **Insider Threat**: Unauthorized access by internal users
- **Phishing Email**: Email-based attacks and credential harvesting
- **Ransomware**: Ransomware deployment and encryption activities
- **Data Exfiltration**: Unauthorized data transfers
- **Privilege Escalation**: Unauthorized privilege increases
- **Lateral Movement**: Network traversal by attackers

Each scenario has:
- Environment knowledge (what the simulated DB knows)
- Expected indicators (what the agent should discover)
- Difficulty level (1-10)

See `src/scenarios.py` for details and to add new scenarios.

## Workflow

### Training Loop

1. **Collect Episodes**: Run agent investigations on various scenarios
   - All LLM calls are logged to OpenPipe automatically
   - Episode results saved locally for analysis

2. **Review Data**: Check logged requests in OpenPipe dashboard
   - Filter by tags (agent, environment, reward)
   - Review conversation quality
   - Export or import to datasets

3. **Create Dataset**: Organize training data
   - Create dataset via script or dashboard
   - Add episodes as training entries
   - Split into train/test sets

4. **Fine-Tune**: Train models on collected data
   - Create fine-tune jobs for agent, environment, or reward models
   - Monitor training progress
   - Evaluate model performance

5. **Iterate**: Use fine-tuned models to collect better data
   - Replace base models with fine-tuned versions
   - Collect new episodes
   - Continue improving

## OpenPipe Integration

This project uses OpenPipe for:
- **Automatic Logging**: All LLM calls are logged via the SDK
- **Data Collection**: Training data is collected automatically
- **Dataset Management**: Create and manage datasets programmatically
- **Fine-Tuning**: Train models on collected data

### Tags Used

- `watson-agent`: Agent LLM calls
- `watson-environment`: Environment LLM calls
- `watson-reward`: Reward LLM calls

Additional tags include `scenario_id`, `scenario_type`, and `episode` for filtering.

## Configuration

Edit `src/config.py` or set environment variables to configure:

- Model choices (agent, environment, reward)
- OpenPipe settings
- Component tags
- Tool call limits

## Next Steps

1. **Expand Scenarios**: Add more attack scenarios (target: 10-100)
2. **RL Training**: Implement RL algorithm (PPO, DQN, etc.) for policy optimization
3. **Sim2Real Transfer**: Build translation layer for real log systems
4. **Evaluation**: Measure detection accuracy and query efficiency
5. **Scaling**: Expand to production deployment

See `agents.md` for detailed research plan and implementation phases.

## Notes

- The agent should feel like it's interacting with a real database, even in simulation
- Translation layer must be bidirectional and lossless (or near-lossless)
- Reward model needs to balance attack detection with query efficiency
- Consider curriculum learning: start with simple scenarios, progress to complex ones

## License

[Add your license here]
