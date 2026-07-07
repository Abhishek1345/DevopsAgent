from dataclasses import dataclass,field
from pathlib import Path
@dataclass
class ApplicationInfo:
 absolute_path: Path=None
 relative_path: Path=None
 manifest_file:Path=None
 language: str = "Unknown"
 framework: str= "Unknown"
 package_manager: str="Unknown"
 databse: str="Unknown"
 has_dockerfile: bool=False


@dataclass
class ProjectInfo:
    project_name: str = ""
    apps_info:list[ApplicationInfo]=field(default_factory=list)
    has_compose: bool = False
    has_github_workflow: bool = False
