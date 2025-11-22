"""Color utilities for terminal output."""
from colorama import Fore, Style, init

# Initialize colorama for cross-platform support
init(autoreset=True)


class Colors:
    """Color constants for terminal output."""
    # Agent queries
    QUERY = Fore.CYAN
    # Database responses
    RESPONSE = Fore.GREEN
    # Rewards
    REWARD_POSITIVE = Fore.GREEN
    REWARD_NEGATIVE = Fore.RED
    REWARD_NEUTRAL = Fore.YELLOW
    # Headers
    HEADER = Fore.MAGENTA
    # Reports
    REPORT = Fore.BLUE
    # Reset
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT


def colorize(text: str, color: str) -> str:
    """Apply color to text."""
    return f"{color}{text}{Style.RESET_ALL}"

