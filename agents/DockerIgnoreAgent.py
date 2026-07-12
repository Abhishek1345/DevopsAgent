from llm.llm import llm
import json
from models.project_info import ProjectInfo,ApplicationInfo
from langchain_core.messages import SystemMessage,HumanMessage
from graph.state import State

def docker_ignore_agent(state:State)->State:
    app_info=state['project_info'].apps_info[state['application_index']]
    state['application_index']+=1
    system_prompt="""you are a Devops architect. Using the given project info 
    generate an approprate .dockerignore file. Generate only the file content.
    Do Not Enclose the file content in markdown code blocks.
    The content will be directly written on a file
    """
    if not app_info.has_dockerfile:
        user_msg={
            "language":app_info.language,
            "framework":app_info.framework,
            "package_manager":app_info.package_manager,
        }
        response=llm.invoke([SystemMessage(content=system_prompt),HumanMessage(content=json.dumps(user_msg))])
        dockerignore=response.content[0]['text']
        state['generated_files'].append({"file":app_info.absolute_path/".dockerignore","content":dockerignore})
       
    return state
    

        

