"""Attack scenario definitions for Watson training."""
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AttackScenario:
    """Represents an attack scenario for training."""
    id: str
    name: str
    description: str
    attack_type: str
    # Knowledge that the environment LLM should have about this attack
    environment_knowledge: str
    # Expected indicators that the agent should discover
    expected_indicators: List[str]
    # Difficulty level (1-10)
    difficulty: int


# Initial set of attack scenarios
ATTACK_SCENARIOS: List[AttackScenario] = [
    AttackScenario(
        id="insider-threat-001",
        name="Unauthorized Access by Internal User",
        description="An internal employee accesses sensitive data outside their normal working hours and role",
        attack_type="Insider Threat",
        environment_knowledge="""
        The following log entries exist:
        - User 'john.doe@company.com' (role: 'analyst') accessed 'customer-db' at 2024-01-15 02:30:00 UTC
        - User 'john.doe@company.com' accessed 'financial-records' at 2024-01-15 02:35:00 UTC
        - User 'john.doe@company.com' accessed 'employee-pii' at 2024-01-15 02:40:00 UTC
        - Normal working hours for this user are 09:00-17:00 UTC
        - User's role 'analyst' does not have permission to access 'financial-records' or 'employee-pii'
        - All accesses occurred from IP address 192.168.1.100 (office network)
        - No other users accessed these systems during this time window
        """,
        expected_indicators=[
            "Access outside normal hours",
            "Access to unauthorized resources",
            "Multiple sensitive database accesses in short time window"
        ],
        difficulty=3
    ),
    AttackScenario(
        id="phishing-001",
        name="Credential Harvesting via Phishing",
        description="Attackers send phishing emails and harvest credentials from multiple employees",
        attack_type="Phishing Email",
        environment_knowledge="""
        The following log entries exist:
        - Email sent from 'noreply@company-security.com' to 50 employees at 2024-01-15 10:00:00 UTC
        - 12 employees clicked the link in the email within 2 hours
        - 8 employees entered credentials on the phishing site
        - Failed login attempts increased by 300% starting at 2024-01-15 14:00:00 UTC
        - 3 accounts were successfully compromised: 'alice.smith@company.com', 'bob.jones@company.com', 'carol.white@company.com'
        - Compromised accounts show logins from new IP addresses: 203.0.113.45, 203.0.113.46, 203.0.113.47
        - These IPs are geolocated to a different country than the normal user locations
        - Email domain 'company-security.com' is not owned by the company
        """,
        expected_indicators=[
            "Suspicious email domain",
            "Multiple credential entries on phishing site",
            "Failed login spike",
            "Logins from new IP addresses",
            "Geographic anomalies"
        ],
        difficulty=5
    ),
    AttackScenario(
        id="ransomware-001",
        name="Ransomware Deployment",
        description="Ransomware is deployed and begins encrypting files across the network",
        attack_type="Ransomware",
        environment_knowledge="""
        The following log entries exist:
        - User 'mary.johnson@company.com' opened email attachment 'invoice.pdf.exe' at 2024-01-15 11:00:00 UTC
        - Process 'encryptor.exe' started on workstation WS-0421 at 2024-01-15 11:05:00 UTC
        - File encryption activity detected: 5000 files encrypted in first 10 minutes
        - Network shares accessed: \\\\fileserver01\\shared, \\\\fileserver02\\backup
        - Encryption activity spread to 15 workstations within 30 minutes
        - Ransom note file 'READ_ME.txt' created on multiple systems
        - Outbound connections to IP 198.51.100.42 (known C2 server)
        - Antivirus alerts suppressed on affected systems
        """,
        expected_indicators=[
            "Suspicious executable execution",
            "Mass file encryption",
            "Network share access",
            "Ransom note creation",
            "C2 server communication",
            "AV suppression"
        ],
        difficulty=7
    ),
    AttackScenario(
        id="data-exfil-001",
        name="Unauthorized Data Exfiltration",
        description="Large volumes of sensitive data are exfiltrated to external servers",
        attack_type="Data Exfiltration",
        environment_knowledge="""
        The following log entries exist:
        - User 'david.brown@company.com' accessed 'customer-database' at 2024-01-15 09:00:00 UTC
        - Large data export initiated: 2.5 GB exported to local file 'export_20240115.csv'
        - File compressed to 'export_20240115.zip' (500 MB) at 2024-01-15 09:30:00 UTC
        - Outbound HTTPS connection to IP 192.0.2.100 (external server) at 2024-01-15 09:35:00 UTC
        - 450 MB transferred over 15 minutes (unusual for this user)
        - User's normal data access pattern is < 10 MB per day
        - External IP 192.0.2.100 is not in approved vendor list
        - Data transfer occurred during business hours but user was on vacation
        """,
        expected_indicators=[
            "Unusually large data export",
            "Data compression",
            "Outbound transfer to unknown IP",
            "Anomalous user behavior",
            "Transfer during unusual time"
        ],
        difficulty=6
    ),
    AttackScenario(
        id="privilege-escalation-001",
        name="Unauthorized Privilege Escalation",
        description="An attacker escalates privileges to gain administrative access",
        attack_type="Privilege Escalation",
        environment_knowledge="""
        The following log entries exist:
        - User 'frank.wilson@company.com' (role: 'developer') logged in at 2024-01-15 08:00:00 UTC
        - User executed 'sudo su -' command at 2024-01-15 08:15:00 UTC (unusual for this user)
        - User added themselves to 'admin' group at 2024-01-15 08:16:00 UTC
        - User accessed 'admin-panel' at 2024-01-15 08:20:00 UTC
        - User modified 'user-permissions' table in database at 2024-01-15 08:25:00 UTC
        - User created new admin account 'temp_admin' at 2024-01-15 08:30:00 UTC
        - Original user 'frank.wilson@company.com' has no history of privilege escalation attempts
        - All actions occurred from IP 198.51.100.10 (not user's normal IP range)
        """,
        expected_indicators=[
            "Privilege escalation command execution",
            "Group membership changes",
            "Admin panel access",
            "Permission modifications",
            "New admin account creation",
            "IP address anomaly"
        ],
        difficulty=8
    ),
    AttackScenario(
        id="lateral-movement-001",
        name="Network Lateral Movement",
        description="Attacker moves laterally through the network after initial compromise",
        attack_type="Lateral Movement",
        environment_knowledge="""
        The following log entries exist:
        - Initial compromise: User 'grace.lee@company.com' credentials used from IP 203.0.113.50 at 2024-01-15 10:00:00 UTC
        - SMB connection from compromised workstation WS-0123 to WS-0456 at 2024-01-15 10:15:00 UTC
        - SMB connection from WS-0456 to WS-0789 at 2024-01-15 10:20:00 UTC
        - SMB connection from WS-0789 to database-server DB-001 at 2024-01-15 10:25:00 UTC
        - Pass-the-hash attack detected: NTLM hash reuse across multiple systems
        - WMI queries executed from WS-0123 to enumerate network resources
        - Remote service creation on WS-0456 and WS-0789
        - All lateral movement occurred within 30 minutes
        - Target database-server DB-001 contains sensitive customer data
        """,
        expected_indicators=[
            "SMB connections between workstations",
            "Pass-the-hash activity",
            "WMI enumeration",
            "Remote service creation",
            "Progressive movement toward sensitive systems",
            "Rapid lateral movement"
        ],
        difficulty=9
    ),
]


def get_scenario_by_id(scenario_id: str) -> AttackScenario:
    """Get an attack scenario by its ID."""
    for scenario in ATTACK_SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise ValueError(f"Scenario {scenario_id} not found")


def get_scenarios_by_difficulty(max_difficulty: int) -> List[AttackScenario]:
    """Get all scenarios with difficulty <= max_difficulty."""
    return [s for s in ATTACK_SCENARIOS if s.difficulty <= max_difficulty]

