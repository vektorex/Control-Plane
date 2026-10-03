# @ai-work-layer/sdk (Official JavaScript SDK)

Official JavaScript SDK for the AI Work Layer Public API. Provides programmatic access to orchestrate tasks, execute workflows, manage multimodal artifacts, retrieve knowledge graphs, and receive verified webhooks.

## Installation

```bash
npm install @ai-work-layer/sdk
```

## Quickstart

```javascript
import { AIWorkLayerClient } from "@ai-work-layer/sdk";

const client = new AIWorkLayerClient({
  apiKey: process.env.AWL_API_KEY, // e.g., awl_dev_...
  baseUrl: "https://api.yourdomain.com/api/v1",
});

// Run a task
const taskRun = await client.tasks.run("task-uuid-here", {
  input: "Summarize recent quarterly telemetry findings.",
  stream: false,
});
console.log("Run started:", taskRun.run_id);

// Retrieve result
const result = await client.runs.result(taskRun.run_id);
console.log("Output:", result.output);
```

## Webhook Verification

```javascript
import { verifyWebhookSignature } from "@ai-work-layer/sdk/webhooks";

const isValid = verifyWebhookSignature(
  rawBodyString,
  req.headers["x-awl-signature"],
  process.env.AWL_WEBHOOK_SECRET,
  300 // 5-minute replay tolerance
);

if (!isValid) {
  res.status(401).send("Invalid signature");
}
```

## Important Security Rules

- **Never embed API keys in browser bundles or client-side JavaScript.**
- **Always keep your webhook signing secrets secure.**
- The Public API provides controlled programmatic access to the platform. API availability, limits, and capabilities are subject to the platform's configured policies and operational state.
