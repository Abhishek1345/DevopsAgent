from scanner.scanner import RepositoryScanner
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
from graph.Graph import ready_graph

def run_agent(repo_path:Path):
    scanner = RepositoryScanner(repo_path)

    info=scanner.scan()
    print(info.project_name)
    print("has compose=",info.has_compose)
    print("has github workflows=",info.has_github_workflow)
    for app in info.apps_info:
        print("Application Info")
        print("\t Application path=",app.absolute_path)
        print("\t relative path",app.relative_path)
        print("\t language=",app.language)
        print("\t framwork=",app.framework)
        print("\t package_manager=",app.package_manager)
        print("\t database=",app.database)
        print("\t port=",app.port)
        print("\t has dockerfile:",app.has_dockerfile)


    ready_graph.invoke({"project_info":info,"application_index":0,"generated_files":[]})



