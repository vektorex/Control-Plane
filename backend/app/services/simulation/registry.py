"""
Simulation Registry for Step 41: AI Agent Simulation.
Maintains available scenarios, fault profiles, and assertion definitions.
"""
from typing import Any, Dict, List, Optional
from backend.app.services.simulation.scenario import BUILTIN_SCENARIO_TEMPLATES


class SimulationRegistry:
    """Provides access to registered built-in scenarios and default templates."""

    @classmethod
    def get_builtin_scenarios(cls) -> List[Dict[str, Any]]:
        return list(BUILTIN_SCENARIO_TEMPLATES)

    @classmethod
    def get_builtin_scenario(cls, name: str) -> Optional[Dict[str, Any]]:
        for s in BUILTIN_SCENARIO_TEMPLATES:
            if s["name"].lower() == name.lower():
                return dict(s)
        return None
