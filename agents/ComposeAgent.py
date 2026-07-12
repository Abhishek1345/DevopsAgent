from llm.llm import llm
import json
from models.project_info import ProjectInfo,ApplicationInfo
from langchain_core.messages import SystemMessage,HumanMessage
from graph.state import State

def compose_agent(state:State)->State:
    project_info:ProjectInfo=state['project_info']
    system_prompt="""you are a Devops architect. Using the given project info 
    generate an approprate docker compose.yaml file . Generate only the file content.
    Do Not Enclose the content in markdown code blocks.
    The content will be directly written on a file
    """
    if not project_info.has_compose:
        services=[]
        for app_info in project_info.apps_info:
            dict={
                "language":app_info.language,
                "relative-path":app_info.relative_path.as_posix(),
                "package-manager":app_info.package_manager,
                "database":app_info.database,
                "port":app_info.port
            }
            services.append(dict)
        response=llm.invoke([SystemMessage(content=system_prompt),HumanMessage(content=json.dumps(services))])
        composefile=response.content[0]['text']
        state['generated_files'].append({"file":project_info.project_path/"compose.yaml","content":composefile})
        return state
        

        

