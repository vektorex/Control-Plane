# ai-work-layer (Official Python SDK)

Official Python SDK for the AI Work Layer Public API. Provides programmatic access to orchestrate tasks, execute workflows, manage multimodal artifacts, retrieve knowledge graphs, and receive verified webhooks.

## Installation

```bash
pip install ai-work-layer
```

## Quickstart

```python
import os
from ai_work_layer import Client

client = Client(
    api_key=os.environ.get("AWL_API_KEY"),
    base_url="https://api.yourdomain.com/api/v1",
)

# Run a task
run = client.tasks.run(
    task_id="00000000-0000-0000-0000-000000000000",
    input_text="Generate quarterly report summary.",
)
print("Run ID:", run["run_id"])

# Get result
result = client.runs.result(run["run_id"])
print("Result output:", result["output"])
```

## Webhook Signature Verification

```python
from ai_work_layer import verify_webhook_signature

is_valid = verify_webhook_signature(
    payload=raw_request_body_bytes,
    signature_header=request.headers.get("X-AWL-Signature"),
    secret=os.environ.get("AWL_WEBHOOK_SECRET"),
    tolerance_seconds=300,
)

if not is_valid:
    raise ValueError("Unauthorized webhook signature")
```

## Security Notice

- **Never embed API credentials directly in source code.**
- The Public API provides controlled programmatic access to the platform. API availability, limits, and capabilities are subject to the platform's configured policies and operational state.
