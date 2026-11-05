class DecisionEventDispatcher:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        
    def dispatch(self, event_type, payload):
        self.event_bus.publish(f"decision.{event_type}", payload)
