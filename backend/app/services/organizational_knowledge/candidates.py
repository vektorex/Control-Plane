class KnowledgeCandidateExtractor:
    def extract_from_decision(self, decision):
        pass

class RuleBasedKnowledgeExtractor(KnowledgeCandidateExtractor):
    def extract(self, source):
        pass

class AIKnowledgeExtractor(KnowledgeCandidateExtractor):
    def extract(self, source, context):
        pass
