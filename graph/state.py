from typing import TypedDict,Annotated
from models.project_info import ProjectInfo,ApplicationInfo
from langgraph.graph.message import add_messages
class State(TypedDict):
    project_info:ProjectInfo
    application_index:int=0
    tasks:list
    generated_files:list
