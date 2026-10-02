"""
Template system for Step 25 notifications and emails.
Safe variable substitution without arbitrary code execution.
"""
import html
import re
from typing import Any, Dict


class NotificationTemplateEngine:
    """
    Renders safe notification titles, bodies, and HTML emails.
    Replaces {{variable.path}} patterns from a context dictionary safely.
    """

    VARIABLE_REGEX = re.compile(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}")

    BUILTIN_TEMPLATES = {
        "workflow.completed": {
            "title": "Workflow Completed: {{workflow.name}}",
            "body": "Workflow '{{workflow.name}}' completed successfully in {{workflow.duration_ms}}ms with status {{workflow.status}}.",
        },
        "workflow.failed": {
            "title": "Workflow Failed: {{workflow.name}}",
            "body": "Workflow '{{workflow.name}}' encountered an error: {{error.message}}.",
        },
        "workflow.waiting_for_approval": {
            "title": "Action Required: Approval Needed for {{workflow.name}}",
            "body": "Workflow '{{workflow.name}}' paused at step '{{step.name}}' and requires human authorization to proceed.",
        },
        "job.failed": {
            "title": "Background Job Failed: {{job.type}}",
            "body": "Job {{job.id}} ({{job.type}}) failed permanently after {{job.attempts}} attempts: {{error.message}}.",
        },
        "evaluation.regression_detected": {
            "title": "Evaluation Regression Detected: {{experiment.name}}",
            "body": "Regression check failed for experiment '{{experiment.name}}' against baseline on dataset '{{dataset.name}}'.",
        },
        "document.processing_completed": {
            "title": "Document Processed: {{document.filename}}",
            "body": "Ingestion pipeline completed for '{{document.filename}}' with {{document.chunk_count}} chunks indexed.",
        },
        "document.processing_failed": {
            "title": "Document Processing Failed: {{document.filename}}",
            "body": "Ingestion pipeline failed for document '{{document.filename}}': {{error.message}}.",
        },
        "trigger.failed": {
            "title": "Trigger Execution Failed: {{trigger.name}}",
            "body": "Trigger '{{trigger.name}}' failed to execute target workflow: {{error.message}}.",
        },
        "replay.completed": {
            "title": "Replay Completed: {{replay.id}}",
            "body": "Execution replay completed with status {{replay.status}}.",
        },
        "replay.failed": {
            "title": "Replay Failed: {{replay.id}}",
            "body": "Execution replay failed: {{error.message}}.",
        },
        "connector.failed": {
            "title": "Connector Operation Failed: {{connector.name}}",
            "body": "Operation '{{connector.operation}}' on connector '{{connector.name}}' failed: {{error.message}}.",
        },
    }

    @classmethod
    def render(cls, template_str: str, context: Dict[str, Any]) -> str:
        """
        Safely replaces variables like {{workflow.name}} with values from context dict.
        Unknown variables resolve to an empty string.
        """
        if not template_str:
            return ""

        def _resolve(match):
            key_path = match.group(1).split(".")
            curr = context
            for k in key_path:
                if isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    return ""
            return str(curr) if curr is not None else ""

        return cls.VARIABLE_REGEX.sub(_resolve, template_str)

    @classmethod
    def render_email_html(cls, title: str, body: str, context: Dict[str, Any]) -> str:
        """
        Renders a polished, responsive HTML email layout for transactional delivery.
        """
        safe_title = html.escape(cls.render(title, context))
        safe_body = html.escape(cls.render(body, context))
        app_url = context.get("app_url", "https://app.aiworklayer.internal")

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #080b12; color: #f8fafc; margin: 0; padding: 24px; }}
    .container {{ max-width: 600px; margin: 0 auto; background-color: #0f172a; border-radius: 12px; border: 1px solid #1e293b; overflow: hidden; }}
    .header {{ padding: 24px; background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%); border-bottom: 1px solid #1e293b; }}
    .header h1 {{ margin: 0; font-size: 18px; color: #ffffff; font-weight: 700; }}
    .content {{ padding: 24px; font-size: 14px; line-height: 1.6; color: #cbd5e1; }}
    .footer {{ padding: 16px 24px; background-color: #07090e; border-top: 1px solid #1e293b; font-size: 12px; color: #64748b; text-align: center; }}
    .button {{ display: inline-block; padding: 10px 20px; background-color: #4f46e5; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Work Layer Notification</h1>
    </div>
    <div class="content">
      <h2 style="font-size: 16px; color: #e2e8f0; margin-top: 0;">{safe_title}</h2>
      <p>{safe_body}</p>
      <a href="{app_url}" class="button">View in AI Work Layer</a>
    </div>
    <div class="footer">
      AI Work Layer Orchestration Engine • Automated Notification
    </div>
  </div>
</body>
</html>"""
