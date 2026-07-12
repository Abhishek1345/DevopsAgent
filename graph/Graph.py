from langgraph.graph import StateGraph,START,END
from graph.state import State
from graph.writer import write
from agents.DockerAgent import docker_agent
def docker_complete(state:State)->State:
    if state["application_index"]>=len(state["project_info"].apps_info):
        return "continue"
    else:
        return "loop"
graph=StateGraph(State)
graph.add_node("docker_agent",docker_agent)
graph.add_node("writer",write)
graph.add_edge(START,"docker_agent")
graph.add_conditional_edges(
    "docker_agent",
    docker_complete,
    {
    "loop":"docker_agent",
    "continue":"writer"
    }
)
graph.add_edge("writer",END)
ready_graph=graph.compile()
