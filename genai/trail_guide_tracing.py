"""Trail Guide AI Assistant with hierarchical OpenTelemetry tracing.

Span hierarchy:
    trail_guide_session
      └─ recommend_hike
           └─ recommend_model_call
                └─ chat gpt-5-mini   (auto-created by the OpenAI instrumentation)

Requires:
    uv add azure-monitor-opentelemetry opentelemetry-instrumentation-openai-v2
Env (.env): FOUNDRY_PROJECT_ENDPOINT
"""
import os
import time

import dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

dotenv.load_dotenv(".env", override=True)

MODEL = "gpt-5-mini"  # must match the deployment name in terraform/foundry/main.tf

# Enable automatic tracing for all OpenAI SDK calls
OpenAIInstrumentor().instrument()

# Connect to the Foundry project
project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# Configure Azure Monitor (Application Insights linked to the project)
telemetry = project_client.telemetry
get_cs = getattr(telemetry, "get_application_insights_connection_string", None) or getattr(
    telemetry, "get_connection_string"
)
configure_azure_monitor(connection_string=get_cs())

tracer = trace.get_tracer(__name__)
openai_client = project_client.get_openai_client()


def call_model(system_prompt: str, user_prompt: str, span_name: str) -> str:
    """Model call wrapper that adds timing and metadata to a span."""
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("prompt.user", user_prompt)
        start_time = time.time()

        # Automatically traced by the OpenAI instrumentation (child span)
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        duration = time.time() - start_time
        output = response.choices[0].message.content or ""
        span.set_attribute("response.time", duration)
        span.set_attribute("response.tokens", len(output.split()))
        return output


def recommend_hike(preferences: str) -> str:
    with tracer.start_as_current_span("recommend_hike") as span:
        prompt = f"""
        Recommend a named hiking trail based on the following user preferences.
        Provide only the name of the trail and a one-sentence summary.
        Preferences: {preferences}
        """
        response = call_model(
            "You are an expert hiking trail recommender.",
            prompt,
            "recommend_model_call",
        )
        result = response.strip()
        span.set_attribute("hike_recommendation", result)
        return result


def trail_guide_session(user_preferences: str) -> str:
    with tracer.start_as_current_span("trail_guide_session") as session_span:
        session_id = f"session_{int(time.time())}"
        session_span.set_attribute("session.id", session_id)

        print("--- Trail Guide AI Assistant ---")
        hike = recommend_hike(user_preferences)
        print(f"✅ Recommended Hike: {hike}")

        session_span.set_attribute("session.success", True)
        print(f"🔍 Trace ID available for session: {session_id}")
        return hike


if __name__ == "__main__":
    trail_guide_session("I want a moderate day hike with lake views and fall colors.")
    # Make sure spans are exported before the process exits
    trace.get_tracer_provider().force_flush()
