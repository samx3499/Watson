# Setup Guide

## Quick Start

1. **Install dependencies**:
   
   Using `uv` (recommended):
   ```bash
   # Install uv if you haven't already: https://github.com/astral-sh/uv
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   
   Create a `.env` file:
   ```bash
   OPENAI_API_KEY=sk-...
   OPENPIPE_API_KEY=opk-...
   ```
   
   Get your OpenPipe API key from: https://app.openpipe.ai/settings

3. **Test the setup**:
   ```bash
   python example_run.py
   ```

## Detailed Setup

### 1. OpenPipe Account Setup

1. Go to https://app.openpipe.ai/
2. Sign up with GitHub (recommended)
3. Navigate to Settings: https://app.openpipe.ai/settings
4. Copy your Project API Key (starts with `opk-`)

### 2. OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
OPENPIPE_API_KEY=opk-your-key-here

# Optional - Model configurations
AGENT_MODEL=gpt-4
ENVIRONMENT_MODEL=gpt-4
REWARD_MODEL=gpt-4
```

### 4. Verify Installation

Run the example script to verify everything works:

```bash
python example_run.py
```

This will:
- Validate your configuration
- Run a single episode on an attack scenario
- Show the results and reward breakdown

## Next Steps

Once setup is complete, you can:

1. **Collect training data**:
   ```bash
   python scripts/collect_data.py --episodes-per-scenario 5
   ```

2. **View logged requests** in OpenPipe dashboard:
   - Go to https://app.openpipe.ai/request-logs
   - Filter by tags: `watson-agent`, `watson-environment`, `watson-reward`

3. **Create datasets and fine-tune models** (see README.md)

## Troubleshooting

### "Configuration error: OPENAI_API_KEY is required"

Make sure your `.env` file exists and contains the required keys. The file should be in the project root directory.

### "OpenPipe API error"

- Verify your OpenPipe API key is correct
- Check that you're using the correct base URL (default: https://app.openpipe.ai/api/v1)
- Ensure your OpenPipe account is active

### Import errors

Make sure you've installed all dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

If you're using `uv`, it automatically manages the virtual environment. If using pip, make sure your virtual environment is activated.

