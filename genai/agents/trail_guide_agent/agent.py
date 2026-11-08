from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import PromptAgentDefinition
import os
import dotenv
from pathlib import Path

dotenv.load_dotenv(".env", override=True)

PROMPT_VERSION = "v3"
AGENT_NAME = "trail-guide-agent"
MODEL = "gpt-5-mini"  # must match the deployment name in terraform/foundry/main.tf

# Read instructions from prompt file
prompt_file = Path(__file__).parent / 'prompts' / f'{PROMPT_VERSION}_instructions.txt'
with open(prompt_file, 'r') as f:
    instructions = f.read().strip()

# Initialize client
client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

agent = client.agents.create_version(
    agent_name=AGENT_NAME,
    definition=PromptAgentDefinition(
        model=MODEL, 
        instructions=instructions,
    ),
)

print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")