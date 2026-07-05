
from pathlib import Path
from models.project_info import *


class RepositoryScanner:
    ignored_folders = {".github", ".vscode", "node_modules"}



    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.folders = [
    item for item in self.repo_path.rglob("*") 
    if item.is_dir() and not any(ignored in item.parts for ignored in self.ignored_folders)
                       ]
        self.folders.append(self.repo_path)
    def validate(self):
     if not self.repo_path.exists():
        raise Exception("Repository does not exist")
     
    def detect_manifest(self,folder):
       manifests={
          "pyproject.toml":"Python",
          "requirements.txt":"Python",
          "Cargo.toml":"Rust",
          "package.json":"node.js",
          "go.mod":"Go",
          "composer.json":"PHP",
          "pom.xml":"Java"
       }
       for file,lang in manifests.items():
          manifest=folder/file
          if(manifest.exists()):
             return [file,lang]

       return None
    
    def detect_dockerfile(self,app_info:ApplicationInfo):
       app_path=app_info.application_path
       dockerfile=app_path/"Dockerfile"
       app_info.has_dockerfile=dockerfile.exists()

    def detect_Applications(self,info:ProjectInfo):
       for folder in self.folders:
          manifest=self.detect_manifest(folder)
          if(manifest is not None):
             file,lang=manifest
             app_info=ApplicationInfo()
             app_info.application_path=folder
             app_info.language=lang
             self.detect_dockerfile(app_info)
             info.apps_info.append(app_info)

    def detect_compose(self,info:ProjectInfo):
     compose_files = [

    "docker-compose.yml",

    "docker-compose.yaml",

    "compose.yml",

    "compose.yaml"

                      ]
     for file in compose_files:
      composefile=self.repo_path/file
      info.has_compose=composefile.exists()
      if(info.has_compose==True):
         break


    def detect_github_workflow(self,info:ProjectInfo):
       workflow=self.repo_path/".github"/"workflows"
       info.has_github_workflow=workflow.exists()

    def scan(self):
        self.validate()
        info=ProjectInfo()
        info.project_name=self.repo_path.name
        self.detect_compose(info)
        self.detect_github_workflow(info)
        self.detect_Applications(info)
        return info
     