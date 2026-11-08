import os
import sys
import time
import json 
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from openai.types.eval_create_params import DataSourceConfigCustom
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileID,
)

load_dotenv(".env", override=True)

ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
MODEL = "gpt-5-mini"
DATASET = "trail-guide-evaluation-dataset"
DATASET_VERSION = "1"
EVAL_NAME = "Trail Guide Quality Evaluation"

foundry_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=DefaultAzureCredential(),
)

client = foundry_client.get_openai_client()


def get_eval_by_name(client, name):
    """Return the most recently created eval with this name, or None.

    The API only retrieves evals by ID, so list them and filter on the name.
    """
    matches = [ev for ev in client.evals.list(limit=100) if ev.name == name]
    return max(matches, key=lambda ev: ev.created_at) if matches else None



# -------------------------------------------------
#   Upload dataset
# -------------------------------------------------

dataset_path = Path(__file__).parent.parent.parent.parent \
                     / "data" / "trail_guide_evaluation_dataset.jsonl"


if not dataset_path.exists():
    raise FileNotFoundError(
        f"Dataset not found at {dataset_path}.\n"
        "Make sure you are running the script from the repository root."
    )

try:
    data_id = foundry_client.datasets.upload_file(
        name=DATASET,
        version=DATASET_VERSION,
        file_path=str(dataset_path),
    ).id
    print(f"✓ Dataset uploaded successfully")

except Exception as upload_error:
    if "already exists" in str(upload_error):
        dataset_obj = foundry_client.datasets.get(name=DATASET, version=DATASET_VERSION)
        data_id = dataset_obj.id
        print(f"✓ Using existing dataset")
    else:
        raise



# -------------------------------------------------
#   Create evaluation definition
# -------------------------------------------------

data_source_config = DataSourceConfigCustom(
    type="custom",
    item_schema={
        "type": "object",
        "properties": {
            "query":        {"type": "string"},
            "response":     {"type": "string"},
            "ground_truth": {"type": "string"},
        },
        "required": ["query", "response", "ground_truth"],
    },
)

testing_criteria = [
    {
        "type": "azure_ai_evaluator",
        "name": "intent_resolution",
        "evaluator_name": "builtin.intent_resolution",
        "initialization_parameters": {"deployment_name": MODEL},
        "data_mapping": {
            "query":    "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "relevance",
        "evaluator_name": "builtin.relevance",
        "initialization_parameters": {"deployment_name": MODEL},
        "data_mapping": {
            "query":    "{{item.query}}",
            "response": "{{item.response}}",
        },
    },
    {
        "type": "azure_ai_evaluator",
        "name": "groundedness",
        "evaluator_name": "builtin.groundedness",
        "initialization_parameters": {"deployment_name": MODEL},
        "data_mapping": {
            "query":    "{{item.query}}",
            "response": "{{item.response}}",
            "context":  "{{item.ground_truth}}",
        },
    },
]

eval_object = get_eval_by_name(client, EVAL_NAME)

if eval_object:
    print(f"✓ Using existing evaluation definition ({eval_object.id})")
else:
    eval_object = client.evals.create(
        name=EVAL_NAME,
        data_source_config=data_source_config,
        testing_criteria=testing_criteria,
    )
    print(f"✓ Evaluation definition created ({eval_object.id})")

eval_run = client.evals.runs.create(
    eval_id=eval_object.id,
    name="trail-guide-baseline-eval",
    data_source=CreateEvalJSONLRunDataSourceParam(
        type="jsonl",
        source=SourceFileID(
            type="file_id",
            id=data_id,
        ),
    ),
    metadata={
        "model": MODEL,
        "dataset": DATASET,
        "prompt_version": "v3",
    }
)
print(f"✓ Evaluation run started ({eval_run.id})")



# -------------------------------------------------
#   Wait for results and report them
# -------------------------------------------------

POLL_SECONDS = 15
TIMEOUT_SECONDS = 30 * 60
TERMINAL_STATUSES = {"completed", "failed", "canceled"}

deadline = time.monotonic() + TIMEOUT_SECONDS
while eval_run.status not in TERMINAL_STATUSES:
    if time.monotonic() > deadline:
        sys.exit(f"Timed out after {TIMEOUT_SECONDS}s waiting for run {eval_run.id} "
                 f"(status: {eval_run.status})")
    time.sleep(POLL_SECONDS)
    eval_run = client.evals.runs.retrieve(eval_run.id, eval_id=eval_object.id)
    print(f"  status: {eval_run.status}")

counts = eval_run.result_counts
criteria_results = [
    {"criteria": c.testing_criteria, "passed": c.passed, "failed": c.failed}
    for c in eval_run.per_testing_criteria_results
]
results = {
    "run_id": eval_run.id,
    "eval_id": eval_object.id,
    "status": eval_run.status,
    "report_url": eval_run.report_url,
    "result_counts": counts.model_dump(),
    "per_testing_criteria": criteria_results,
}

output_dir = Path(os.environ.get("EVAL_OUTPUT_DIR", "eval-results"))
output_dir.mkdir(parents=True, exist_ok=True)
(output_dir / "results.json").write_text(json.dumps(results, indent=2))

print(f"\nStatus: {eval_run.status}")
print(f"Passed {counts.passed} / {counts.total} (failed {counts.failed}, errored {counts.errored})")
for c in criteria_results:
    print(f"  {c['criteria']}: {c['passed']} passed, {c['failed']} failed")
print(f"Report: {eval_run.report_url}")

# Markdown summary on the GitHub Actions run page (no-op locally)
summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_file:
    lines = [
        f"### {EVAL_NAME}",
        f"**Status:** {eval_run.status} · **Passed:** {counts.passed}/{counts.total} "
        f"· **Failed:** {counts.failed} · **Errored:** {counts.errored}",
        "",
        "| Criteria | Passed | Failed |",
        "| --- | --- | --- |",
        *(f"| {c['criteria']} | {c['passed']} | {c['failed']} |" for c in criteria_results),
        "",
        f"[Open report in Foundry]({eval_run.report_url})",
    ]
    with open(summary_file, "a") as f:
        f.write("\n".join(lines) + "\n")

if eval_run.status != "completed":
    sys.exit(1)