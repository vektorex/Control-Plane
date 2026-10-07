class BaseReadinessRule:
    def evaluate(self, state, context):
        raise NotImplementedError()

class GovernanceReadinessRule(BaseReadinessRule):
    def evaluate(self, state, context):
        return {"satisfied": True, "blocking": True}

class SecurityReadinessRule(BaseReadinessRule):
    def evaluate(self, state, context):
        return {"satisfied": True, "blocking": True}\n