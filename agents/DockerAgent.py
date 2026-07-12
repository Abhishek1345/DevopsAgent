from llm.llm import llm
import json
from models.project_info import ProjectInfo,ApplicationInfo
from langchain_core.messages import SystemMessage,HumanMessage
from graph.state import State

def docker_agent(state:State)->State:
    app_info=state['project_info'].apps_info[state['application_index']]
    system_prompt="""you are a Devops architect. Using the given project info 
    generate an approprate Dockerfile. Generate only the Dockefile
    Do Not Enclose the Dockerfile content in markdown code blocks.
    The content will be directly written on a file
    """
    if not app_info.has_dockerfile:
        user_msg={
            "language":app_info.language,
            "framework":app_info.framework,
            "package_manager":app_info.package_manager,
            "port":app_info.port
        }
        response=llm.invoke([SystemMessage(content=system_prompt),HumanMessage(content=json.dumps(user_msg))])
        dockerfile=response.content[0]['text']
        state['generated_files'].append({"file":app_info.absolute_path/"Dockerfile","content":dockerfile})
        
    return state
        

        

