"""LangGraph based code generation agent."""

from __future__ import annotations

import multiprocessing
import sys
from typing import Any, Dict
from dataclasses import dataclass

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import Graph, MessageState, END

# Context about available utilities
CONTEXT = (
    "You can call assume_role_get_billing.list_service_usage(account_id) to "
    "retrieve service and usage type costs for the previous month."
)


@dataclass
class CodeState(MessageState):
    """State tracked by the LangGraph agent."""

    task: str
    code: str | None = None
    output: Any | None = None
    error: str | None = None

def generate_code(state: CodeState) -> CodeState:
    """Generate Python code for the requested task.

    Args:
        state: Current state dictionary. Must contain ``task`` and may contain
            ``error`` describing a previous failure.

    Returns:
        Updated state with ``code`` field containing the generated code.
    """
    task = state.task
    error = state.error
    prompt = (
        f"Write a short Python function to {task}.\n"
        f"You have access to assume_role_get_billing.list_service_usage.\n"
    )
    if error:
        prompt += f"\nPrevious error:\n{error}\nPlease correct it."

    llm = ChatOpenAI(model_name="gpt-4.1", temperature=0)
    messages = [HumanMessage(content=CONTEXT + "\n" + prompt)]
    code = llm(messages).content
    state.code = code
    # Clear error from previous iteration
    state.error = None
    return state

def _exec_worker(code: str, queue: multiprocessing.Queue) -> None:
    """Worker function to execute code and put result in queue."""
    restricted_globals = {"__builtins__": {"print": print}}
    try:
        local_vars: Dict[str, Any] = {}
        exec(code, restricted_globals, local_vars)
        queue.put({"success": True, "output": local_vars})
    except Exception as e:  # pragma: no cover - best effort
        queue.put({"success": False, "error": str(e)})

def execute_code(state: CodeState) -> CodeState:
    """Execute generated code safely with a timeout."""
    code = state.code or ""
    queue: multiprocessing.Queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_exec_worker, args=(code, queue))
    proc.start()
    proc.join(timeout=10)
    if proc.is_alive():
        proc.terminate()
        state.error = "Execution timed out"
    else:
        result = queue.get()
        if result.get("success"):
            state.output = result.get("output")
        else:
            state.error = result.get("error")
    return state

def build_graph() -> Any:
    """Create the LangGraph for iterative code generation and execution."""
    graph = Graph()
    graph.add_node("generate", generate_code)
    graph.add_node("execute", execute_code)
    graph.add_edge("generate", "execute")

    def route(state: CodeState) -> str:
        return END if state.output and not state.error else "generate"

    graph.add_conditional_edges("execute", route)
    return graph.compile()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python langgraph_agent.py \"Write code to <task>\"")
        sys.exit(1)
    task = sys.argv[1]
    app = build_graph()
    result: CodeState = app.invoke(CodeState(task=task))
    if result.output is not None:
        print("Execution output:", result.output)
    if result.error is not None:
        print("Final error:", result.error, file=sys.stderr)

if __name__ == "__main__":
    main()

