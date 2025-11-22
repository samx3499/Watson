"""Script to manage OpenPipe datasets and fine-tunes."""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


class OpenPipeClient:
    """Client for interacting with OpenPipe API."""
    
    def __init__(self):
        self.api_key = Config.OPENPIPE_API_KEY
        self.base_url = Config.OPENPIPE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def create_dataset(self, name: str) -> str:
        """Create a new dataset."""
        url = f"{self.base_url}/unstable/dataset/create"
        response = requests.post(
            url,
            headers=self.headers,
            json={"name": name}
        )
        response.raise_for_status()
        return response.json()["datasetId"]
    
    def add_dataset_entries(self, dataset_id: str, entries: List[Dict[str, Any]]) -> None:
        """Add entries to a dataset."""
        url = f"{self.base_url}/unstable/dataset-entry/create"
        response = requests.post(
            url,
            headers=self.headers,
            json={
                "datasetId": dataset_id,
                "entries": entries
            }
        )
        response.raise_for_status()
    
    def create_finetune(
        self,
        dataset_id: str,
        slug: str,
        base_model: str = "meta-llama/Llama-2-13b-hf"
    ) -> str:
        """Create a fine-tune job."""
        url = f"{self.base_url}/unstable/finetune/create"
        response = requests.post(
            url,
            headers=self.headers,
            json={
                "datasetId": dataset_id,
                "slug": slug,
                "baseModel": base_model
            }
        )
        response.raise_for_status()
        return response.json()["id"]
    
    def get_finetune_status(self, finetune_id: str) -> Dict[str, Any]:
        """Get the status of a fine-tune job."""
        url = f"{self.base_url}/unstable/finetune/get"
        response = requests.get(
            url,
            headers=self.headers,
            params={"fineTuneId": finetune_id}
        )
        response.raise_for_status()
        return response.json()


def convert_episode_to_training_format(episode_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert episode data to OpenPipe training format.
    Creates training examples for agent, environment, and reward components.
    """
    training_examples = []
    
    investigation = episode_data.get("investigation", {})
    conversation_history = investigation.get("conversation_history", [])
    
    # Convert agent conversation to training format
    agent_messages = []
    for msg in conversation_history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        
        if role == "assistant":
            if tool_calls:
                # Agent made a tool call
                agent_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                }
                agent_messages.append(agent_msg)
            elif content:
                agent_messages.append({"role": "assistant", "content": content})
        elif role == "tool":
            # Tool response
            agent_messages.append({
                "role": "tool",
                "tool_call_id": msg.get("tool_call_id"),
                "content": msg.get("content", "")
            })
        elif role == "user":
            agent_messages.append({"role": "user", "content": content})
    
    if agent_messages:
        training_examples.append({
            "messages": agent_messages,
            "split": "TRAIN"  # Could be randomized or based on scenario
        })
    
    return training_examples


def load_episodes_from_directory(directory: Path) -> List[Dict[str, Any]]:
    """Load all episode JSON files from a directory."""
    episodes = []
    for episode_file in directory.glob("*_episode_*.json"):
        try:
            with open(episode_file, "r") as f:
                episodes.append(json.load(f))
        except Exception as e:
            print(f"Error loading {episode_file}: {e}")
    return episodes


def main():
    parser = argparse.ArgumentParser(description="Manage OpenPipe datasets and fine-tunes")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create dataset command
    create_dataset_parser = subparsers.add_parser("create-dataset", help="Create a new dataset")
    create_dataset_parser.add_argument("--name", type=str, required=True, help="Dataset name")
    
    # Add entries command
    add_entries_parser = subparsers.add_parser("add-entries", help="Add entries to a dataset")
    add_entries_parser.add_argument("--dataset-id", type=str, required=True, help="Dataset ID")
    add_entries_parser.add_argument("--episodes-dir", type=str, required=True, help="Directory containing episode JSON files")
    
    # Create finetune command
    create_finetune_parser = subparsers.add_parser("create-finetune", help="Create a fine-tune job")
    create_finetune_parser.add_argument("--dataset-id", type=str, required=True, help="Dataset ID")
    create_finetune_parser.add_argument("--slug", type=str, required=True, help="Fine-tune slug/name")
    create_finetune_parser.add_argument(
        "--base-model",
        type=str,
        default="meta-llama/Llama-2-13b-hf",
        help="Base model to fine-tune (default: meta-llama/Llama-2-13b-hf)"
    )
    
    # Check finetune status command
    status_parser = subparsers.add_parser("finetune-status", help="Check fine-tune job status")
    status_parser.add_argument("--finetune-id", type=str, required=True, help="Fine-tune ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    client = OpenPipeClient()
    
    if args.command == "create-dataset":
        dataset_id = client.create_dataset(args.name)
        print(f"Created dataset: {dataset_id}")
        print(f"Name: {args.name}")
    
    elif args.command == "add-entries":
        episodes_dir = Path(args.episodes_dir)
        if not episodes_dir.exists():
            print(f"Error: Directory {episodes_dir} does not exist")
            sys.exit(1)
        
        episodes = load_episodes_from_directory(episodes_dir)
        print(f"Loaded {len(episodes)} episodes")
        
        # Convert to training format
        all_entries = []
        for episode in episodes:
            entries = convert_episode_to_training_format(episode)
            all_entries.extend(entries)
        
        print(f"Converting to {len(all_entries)} training entries...")
        
        # Add entries in batches (OpenPipe may have limits)
        batch_size = 100
        for i in range(0, len(all_entries), batch_size):
            batch = all_entries[i:i + batch_size]
            print(f"Adding batch {i // batch_size + 1} ({len(batch)} entries)...")
            client.add_dataset_entries(args.dataset_id, batch)
            time.sleep(1)  # Rate limiting
        
        print(f"Added {len(all_entries)} entries to dataset {args.dataset_id}")
    
    elif args.command == "create-finetune":
        finetune_id = client.create_finetune(
            args.dataset_id,
            args.slug,
            args.base_model
        )
        print(f"Created fine-tune job: {finetune_id}")
        print(f"Dataset: {args.dataset_id}")
        print(f"Slug: {args.slug}")
        print(f"Base model: {args.base_model}")
    
    elif args.command == "finetune-status":
        status = client.get_finetune_status(args.finetune_id)
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()

