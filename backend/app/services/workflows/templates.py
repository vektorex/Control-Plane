"""
Pre-configured, production-ready built-in workflow templates.
"""
from typing import Dict, List, Optional
from backend.app.services.workflows.schemas import (
    StepType,
    WorkflowDefinition,
    WorkflowStepDefinition,
    WorkflowTemplateResponse,
)


class WorkflowTemplateRegistry:
    """
    Registry of immutable built-in workflow templates.
    """

    @classmethod
    def get_all_templates(cls) -> List[WorkflowTemplateResponse]:
        return [
            cls.get_research_assistant_template(),
            cls.get_document_qa_template(),
            cls.get_summarize_and_verify_template(),
            cls.get_research_report_template(),
        ]

    @classmethod
    def get_template_by_id(cls, template_id: str) -> Optional[WorkflowTemplateResponse]:
        templates = {t.id: t for t in cls.get_all_templates()}
        return templates.get(template_id)

    @classmethod
    def get_research_assistant_template(cls) -> WorkflowTemplateResponse:
        return WorkflowTemplateResponse(
            id="research-assistant",
            name="Research Assistant",
            description="Autonomous web search grounding, project knowledge retrieval, structured generation, and factual verification.",
            category="Research",
            icon="Search",
            definition=WorkflowDefinition(
                name="Research Assistant",
                description="Autonomous web search grounding, project knowledge retrieval, structured generation, and factual verification.",
                version=1,
                input_schema={
                    "query": {
                        "type": "string",
                        "description": "Research question or topic",
                        "required": True,
                    }
                },
                steps=[
                    WorkflowStepDefinition(
                        id="input",
                        name="Capture Query",
                        type=StepType.INPUT,
                        config={},
                    ),
                    WorkflowStepDefinition(
                        id="web_search",
                        name="Live Web Grounding",
                        type=StepType.TOOL,
                        config={
                            "tool_name": "web_search",
                            "parameters": {"query": "{{input.query}}", "limit": 5},
                        },
                    ),
                    WorkflowStepDefinition(
                        id="retrieve_kb",
                        name="Retrieve Project Knowledge",
                        type=StepType.RETRIEVE,
                        config={"top_k": 5, "strategy": "hybrid"},
                    ),
                    WorkflowStepDefinition(
                        id="synthesize",
                        name="Synthesize Analysis",
                        type=StepType.GENERATE,
                        config={
                            "temperature": 0.3,
                            "prompt_template": "Synthesize a thorough, well-structured response to the user's research query: '{{input.query}}' using web and knowledge context.",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="evaluate",
                        name="Verification Check",
                        type=StepType.EVALUATE,
                        config={"mode": "standard"},
                    ),
                    WorkflowStepDefinition(
                        id="output",
                        name="Final Output",
                        type=StepType.OUTPUT,
                        config={"primary_output": "{{steps.synthesize.output}}"},
                    ),
                ],
            ),
        )

    @classmethod
    def get_document_qa_template(cls) -> WorkflowTemplateResponse:
        return WorkflowTemplateResponse(
            id="document-qa",
            name="Document Q&A",
            description="Retrieves relevant grounded document chunks from project knowledge base and verifies answers with strict grounding checks.",
            category="Knowledge Base",
            icon="Files",
            definition=WorkflowDefinition(
                name="Document Q&A",
                description="Retrieves relevant grounded document chunks from project knowledge base and verifies answers with strict grounding checks.",
                version=1,
                input_schema={
                    "question": {
                        "type": "string",
                        "description": "Question to answer from project documents",
                        "required": True,
                    }
                },
                steps=[
                    WorkflowStepDefinition(
                        id="input",
                        name="Input Question",
                        type=StepType.INPUT,
                        config={},
                    ),
                    WorkflowStepDefinition(
                        id="retrieve",
                        name="Hybrid Document Retrieval",
                        type=StepType.RETRIEVE,
                        config={"top_k": 6, "strategy": "hybrid", "scope": "project"},
                    ),
                    WorkflowStepDefinition(
                        id="generate_answer",
                        name="Grounded Answer Generation",
                        type=StepType.GENERATE,
                        config={
                            "temperature": 0.2,
                            "prompt_template": "Answer the following question precisely based strictly on the retrieved document context:\n\n{{input.question}}",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="verify_grounding",
                        name="Grounding & Citation Verification",
                        type=StepType.EVALUATE,
                        config={"mode": "strict"},
                    ),
                    WorkflowStepDefinition(
                        id="output",
                        name="Deliver Answer",
                        type=StepType.OUTPUT,
                        config={"primary_output": "{{steps.generate_answer.output}}"},
                    ),
                ],
            ),
        )

    @classmethod
    def get_summarize_and_verify_template(cls) -> WorkflowTemplateResponse:
        return WorkflowTemplateResponse(
            id="summarize-verify",
            name="Summarize & Verify",
            description="Generates concise or comprehensive summaries, runs completeness evaluation, and conditionally triggers revision if warnings are flagged.",
            category="Content",
            icon="FileText",
            definition=WorkflowDefinition(
                name="Summarize & Verify",
                description="Generates concise or comprehensive summaries, runs completeness evaluation, and conditionally triggers revision if warnings are flagged.",
                version=1,
                input_schema={
                    "content": {
                        "type": "string",
                        "description": "Source text or article to summarize",
                        "required": True,
                    },
                    "length": {
                        "type": "string",
                        "description": "Summary length style (e.g. 'concise', 'detailed', 'bulleted')",
                        "required": False,
                        "default": "concise",
                    },
                },
                steps=[
                    WorkflowStepDefinition(
                        id="input",
                        name="Input Content",
                        type=StepType.INPUT,
                        config={},
                    ),
                    WorkflowStepDefinition(
                        id="generate_summary",
                        name="Generate Summary",
                        type=StepType.GENERATE,
                        config={
                            "temperature": 0.2,
                            "prompt_template": "Provide a {{input.length}} summary capturing all key insights of the following content:\n\n{{input.content}}",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="evaluate_summary",
                        name="Evaluate Completeness & Quality",
                        type=StepType.EVALUATE,
                        config={"mode": "standard"},
                    ),
                    WorkflowStepDefinition(
                        id="check_evaluation",
                        name="Check If Revision Needed",
                        type=StepType.CONDITION,
                        config={
                            "left": "steps.evaluate_summary.status",
                            "operator": "==",
                            "right": "warning",
                            "if_true": "revise_summary",
                            "if_false": "output",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="revise_summary",
                        name="Autonomous Revision",
                        type=StepType.GENERATE,
                        config={
                            "temperature": 0.2,
                            "prompt_template": "Refine and improve the summary addressing completeness concerns:\n\nDraft: {{steps.generate_summary.output}}",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="output",
                        name="Final Verified Summary",
                        type=StepType.OUTPUT,
                        config={"primary_output": "{{steps.generate_summary.output}}"},
                    ),
                ],
            ),
        )

    @classmethod
    def get_research_report_template(cls) -> WorkflowTemplateResponse:
        return WorkflowTemplateResponse(
            id="research-report",
            name="Research Report",
            description="Multi-stage intelligence pipeline: web search, document retrieval, comprehensive draft generation, evaluation, and automated refinement.",
            category="Reports",
            icon="Layers",
            definition=WorkflowDefinition(
                name="Research Report",
                description="Multi-stage intelligence pipeline: web search, document retrieval, comprehensive draft generation, evaluation, and automated refinement.",
                version=1,
                input_schema={
                    "topic": {
                        "type": "string",
                        "description": "Primary topic of the research report",
                        "required": True,
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Target audience (e.g. 'executive', 'technical', 'general')",
                        "required": False,
                        "default": "technical",
                    },
                },
                steps=[
                    WorkflowStepDefinition(
                        id="input",
                        name="Input Parameters",
                        type=StepType.INPUT,
                        config={},
                    ),
                    WorkflowStepDefinition(
                        id="web_research",
                        name="External Web Grounding",
                        type=StepType.TOOL,
                        config={
                            "tool_name": "web_search",
                            "parameters": {"query": "{{input.topic}}", "limit": 6},
                        },
                    ),
                    WorkflowStepDefinition(
                        id="retrieve_docs",
                        name="Internal Context Retrieval",
                        type=StepType.RETRIEVE,
                        config={"top_k": 8, "strategy": "hybrid"},
                    ),
                    WorkflowStepDefinition(
                        id="generate_draft",
                        name="Draft Comprehensive Report",
                        type=StepType.GENERATE,
                        config={
                            "temperature": 0.3,
                            "prompt_template": "Generate an in-depth, structured research report on '{{input.topic}}' tailored for a {{input.target_audience}} audience.",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="evaluate_report",
                        name="Verify Grounding & Quality",
                        type=StepType.EVALUATE,
                        config={"mode": "standard"},
                    ),
                    WorkflowStepDefinition(
                        id="condition_quality",
                        name="Evaluate Pass Condition",
                        type=StepType.CONDITION,
                        config={
                            "left": "steps.evaluate_report.status",
                            "operator": "!=",
                            "right": "passed",
                            "if_true": "refine_draft",
                            "if_false": "output",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="refine_draft",
                        name="Refine & Polish Report",
                        type=StepType.GENERATE,
                        config={
                            "temperature": 0.2,
                            "prompt_template": "Polish and refine the research report addressing all evaluator findings:\n\n{{steps.generate_draft.output}}",
                        },
                    ),
                    WorkflowStepDefinition(
                        id="output",
                        name="Deliver Final Report",
                        type=StepType.OUTPUT,
                        config={"primary_output": "{{steps.generate_draft.output}}"},
                    ),
                ],
            ),
        )
