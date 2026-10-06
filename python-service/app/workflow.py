from typing import TypedDict
from datetime import date
from langgraph.graph import StateGraph, END
from .models import Caller, AnswerResponse
from .policy import PolicyStore
from .model import OfflineModel

class State(TypedDict, total=False):
    question: str
    as_of: date
    caller: Caller
    policies: list
    response: AnswerResponse

class AnswerWorkflow:
    def __init__(self, store: PolicyStore):
        self.store = store
        self.model = OfflineModel()

        def retrieve(state: State):
            return {"policies": self.store.retrieve(state["question"], state["caller"], state["as_of"])}

        def decide(state: State):
            policies = state["policies"]
            # Multiple simultaneously applicable records for same benefit = conflict.
            if len(policies) > 1:
                citations = self.store.citations(policies)
                return {"response": AnswerResponse(status="CONFLICT", answer=None, citations=citations)}
            citations = self.store.citations(policies)
            return {"response": self.model.answer(state["question"], citations)}

        g = StateGraph(State)
        g.add_node("retrieve_policy", retrieve)
        g.add_node("decide", decide)
        g.set_entry_point("retrieve_policy")
        g.add_edge("retrieve_policy", "decide")
        g.add_edge("decide", END)
        self.graph = g.compile()

    def run(self, question: str, as_of: date, caller: Caller):
        return self.graph.invoke({"question": question, "as_of": as_of, "caller": caller})["response"]
