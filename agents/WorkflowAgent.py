from llm.llm import llm
import json
from models.project_info import ProjectInfo,ApplicationInfo
from langchain_core.messages import SystemMessage,HumanMessage
from graph.state import State

def workflow_agent(state:State)->State:
    project_info:ProjectInfo=state['project_info']
    system_prompt="""you are a Devops architect. Using the given project info 
    generate an approprate github actions workflow file for deployment.
    On Every push to the master branch the workflow must build the docker images
    and push to images of each service to docker hub.
    Copy compose.yaml file and ENV_SECRETS stored in github actions 
    secrets to Azure VM via SCP action.store ENV_SECRETS in .env file
    SSH to Azure VM and run the compose file.
    Wherever secrets are required assume that user has stored them in Github Actions secrets.
    Generate only the file content. Do not eclose it in markdown code block.
    Content will be directly written on a file
    """
    if not project_info.has_github_workflow:
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
        workflow_file=response.content[0]['text']
        state['generated_files'].append({"file":project_info.project_path/".github/workflows/deploy.yaml","content":workflow_file})
        
    return state
        

        

