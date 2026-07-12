import json
import os
import re
import tomllib
import xml.etree.ElementTree as ET
from fnmatch import fnmatch
from pathlib import Path
from models.project_info import *

class ApplicationScanner:
   ignored_folders = {".git", ".github", ".vscode", "__pycache__", "node_modules", "dist", "build", "target", ".venv", "venv"}
   max_text_file_bytes = 300_000
   max_files_per_pattern_scan = 300
   framework_dependencies = {
      "Python": {
         "Django": {"django"},
         "FastAPI": {"fastapi"},
         "Flask": {"flask"},
         "Streamlit": {"streamlit"},
      },
      "node.js": {
         "Next.js": {"next"},
         "React": {"react", "react-dom", "vite", "@vitejs/plugin-react"},
         "Express": {"express"},
         "NestJS": {"@nestjs/core", "@nestjs/common"},
         "Angular": {"@angular/core"},
         "Vue": {"vue", "nuxt"},
      },
      "Java": {
         "Spring Boot": {"spring-boot-starter", "spring-boot-starter-web"},
         "Quarkus": {"quarkus"},
      },
      "Go": {
         "Gin": {"github.com/gin-gonic/gin"},
         "Fiber": {"github.com/gofiber/fiber"},
         "Echo": {"github.com/labstack/echo"},
      },
      "PHP": {
         "Laravel": {"laravel/framework"},
         "Symfony": {"symfony/framework-bundle"},
      },
      "Rust": {
         "Actix Web": {"actix-web"},
         "Rocket": {"rocket"},
         "Axum": {"axum"},
      },
   }
   database_dependencies = {
      "PostgreSQL": {"postgres", "postgresql", "psycopg2", "asyncpg", "pg", "org.postgresql:postgresql", "gorm.io/driver/postgres"},
      "MySQL": {"mysql", "mysqlclient", "pymysql", "mysql2", "mysql-connector", "com.mysql:mysql-connector-j", "gorm.io/driver/mysql"},
      "MongoDB": {"mongodb", "mongoose", "pymongo", "motor", "org.mongodb", "go.mongodb.org/mongo-driver"},
      "SQLite": {"sqlite", "sqlite3", "better-sqlite3", "aiosqlite", "gorm.io/driver/sqlite"},
      "Redis": {"redis", "ioredis", "hiredis", "github.com/redis/go-redis"},
   }

   def __init__(self, repo_path:Path,folder:Path):
      self.repo_path=repo_path
      self.application_path=folder

   def _read_text(self,path:Path):
      try:
         if path.stat().st_size > self.max_text_file_bytes:
            return ""
         return path.read_text(encoding="utf-8",errors="ignore")
      except OSError:
         return ""

   def _iter_files(self,patterns,limit=None):
      matched=0
      for root,dirs,files in os.walk(self.application_path):
         dirs[:]=[name for name in dirs if name not in self.ignored_folders]
         for file in files:
            if any(fnmatch(file,pattern) for pattern in patterns):
               yield Path(root)/file
               matched+=1
               if limit and matched>=limit:
                  return

   def _search_files(self,patterns,file_patterns):
      for path in self._iter_files(file_patterns,self.max_files_per_pattern_scan):
         text=self._read_text(path)
         if not text:
            continue
         for label,pattern in patterns:
            if re.search(pattern,text,re.IGNORECASE):
               return label
      return "Unknown"

   def _dependency_names(self):
      names=set()
      package_json=self.application_path/"package.json"
      if package_json.exists():
         try:
            data=json.loads(self._read_text(package_json))
            for key in ("dependencies","devDependencies","peerDependencies","optionalDependencies"):
               names.update((data.get(key) or {}).keys())
         except json.JSONDecodeError:
            pass

      requirements=self.application_path/"requirements.txt"
      if requirements.exists():
         for line in self._read_text(requirements).splitlines():
            line=line.strip()
            if line and not line.startswith("#"):
               name=re.split(r"[<>=~!;\[]",line,1)[0].strip()
               if name:
                  names.add(name.lower())

      pyproject=self.application_path/"pyproject.toml"
      if pyproject.exists():
         try:
            data=tomllib.loads(self._read_text(pyproject))
            project=data.get("project") or {}
            for dep in project.get("dependencies") or []:
               name=re.split(r"[<>=~!;\[]",dep,1)[0].strip()
               if name:
                  names.add(name.lower())
            poetry=((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
            names.update(name.lower() for name in poetry.keys() if name.lower()!="python")
         except tomllib.TOMLDecodeError:
            pass

      composer=self.application_path/"composer.json"
      if composer.exists():
         try:
            data=json.loads(self._read_text(composer))
            names.update((data.get("require") or {}).keys())
            names.update((data.get("require-dev") or {}).keys())
         except json.JSONDecodeError:
            pass

      cargo=self.application_path/"Cargo.toml"
      if cargo.exists():
         try:
            data=tomllib.loads(self._read_text(cargo))
            for key in ("dependencies","dev-dependencies","build-dependencies"):
               names.update((data.get(key) or {}).keys())
         except tomllib.TOMLDecodeError:
            pass

      gomod=self.application_path/"go.mod"
      if gomod.exists():
         for line in self._read_text(gomod).splitlines():
            line=line.strip()
            if line and not line.startswith(("module","go","require","(",")","//")):
               names.add(line.split()[0])

      pom=self.application_path/"pom.xml"
      if pom.exists():
         try:
            root=ET.fromstring(self._read_text(pom))
            for dependency in root.findall(".//{*}dependency"):
               group=(dependency.findtext("{*}groupId") or "").strip()
               artifact=(dependency.findtext("{*}artifactId") or "").strip()
               if artifact:
                  names.add(artifact)
               if group and artifact:
                  names.add(f"{group}:{artifact}")
         except ET.ParseError:
            pass

      return names

   def detect_dockerfile(self,app_info:ApplicationInfo):
       app_path=app_info.absolute_path
       dockerfile=app_path/"Dockerfile"
       app_info.has_dockerfile=dockerfile.exists()

   def detect_package_manager(self,app_info:ApplicationInfo):
      checks=[
         ("package-lock.json","npm"),
         ("pnpm-lock.yaml","pnpm"),
         ("yarn.lock","yarn"),
         ("bun.lockb","bun"),
         ("poetry.lock","Poetry"),
         ("Pipfile.lock","Pipenv"),
         ("uv.lock","uv"),
         ("requirements.txt","pip"),
         ("pom.xml","Maven"),
         ("build.gradle","Gradle"),
         ("build.gradle.kts","Gradle"),
         ("go.mod","Go modules"),
         ("Cargo.lock","Cargo"),
         ("composer.lock","Composer"),
         ("composer.json","Composer"),
      ]
      for file,manager in checks:
         if (self.application_path/file).exists():
            app_info.package_manager=manager
            return
      if app_info.manifest_file:
         fallback={
            "package.json":"npm",
            "pyproject.toml":"pip/Poetry",
            "Cargo.toml":"Cargo",
            "go.mod":"Go modules",
            "pom.xml":"Maven",
         }
         app_info.package_manager=fallback.get(str(app_info.manifest_file),"Unknown")

   def _match_from_dependencies(self,dependency_names,choices):
      normalized={name.lower() for name in dependency_names}
      for label,candidates in choices.items():
         for candidate in candidates:
            candidate=candidate.lower()
            if candidate in normalized or any(candidate in dep for dep in normalized):
               return label
      return "Unknown"

   def detect_framework(self,app_info:ApplicationInfo,dependency_names):
      app_info.framework=self._match_from_dependencies(
         dependency_names,
         self.framework_dependencies.get(app_info.language,{})
      )
      if app_info.framework!="Unknown":
         return

      patterns=[
         ("FastAPI",r"FastAPI\s*\("),
         ("Flask",r"Flask\s*\("),
         ("Django",r"DJANGO_SETTINGS_MODULE|django\."),
         ("Express",r"express\s*\("),
         ("Spring Boot",r"@SpringBootApplication"),
         ("Gin",r"gin\.Default\s*\(|gin\.New\s*\("),
         ("Laravel",r"Illuminate\\"),
         ("Actix Web",r"actix_web"),
      ]
      app_info.framework=self._search_files(patterns,["*.py","*.js","*.jsx","*.ts","*.tsx","*.java","*.go","*.php","*.rs"])

   def detect_database(self,app_info:ApplicationInfo,dependency_names):
      app_info.database=self._match_from_dependencies(dependency_names,self.database_dependencies)
      if app_info.database!="Unknown":
         return

      patterns=[
         ("PostgreSQL",r"postgres(?:ql)?://|POSTGRES_|postgres:"),
         ("MySQL",r"mysql://|MYSQL_|mariadb:|mysql:"),
         ("MongoDB",r"mongodb://|MONGO_|mongo:"),
         ("SQLite",r"sqlite://|\.sqlite|sqlite3"),
         ("Redis",r"redis://|REDIS_|redis:"),
      ]
      app_info.database=self._search_files(patterns,["*.env","*.yml","*.yaml","*.json","*.py","*.js","*.ts","*.java","*.go","*.php","*.rs"])

   def detect_port(self,app_info:ApplicationInfo):
      candidates=[]
      dockerfile=self.application_path/"Dockerfile"
      if dockerfile.exists():
         candidates.extend(int(port) for port in re.findall(r"(?im)^\s*EXPOSE\s+(\d+)",self._read_text(dockerfile)))

      for env_file in self._iter_files([".env","*.env"]):
         candidates.extend(int(port) for port in re.findall(r"(?im)^\s*(?:PORT|APP_PORT|SERVER_PORT)\s*=\s*['\"]?(\d+)",self._read_text(env_file)))

      package_json=self.application_path/"package.json"
      if package_json.exists():
         try:
            data=json.loads(self._read_text(package_json))
            scripts=" ".join((data.get("scripts") or {}).values())
            candidates.extend(int(port) for port in re.findall(r"(?:--port\s+|PORT=|localhost:|127\.0\.0\.1:)(\d+)",scripts))
         except json.JSONDecodeError:
            pass

      port_patterns=[
         r"\.listen\s*\(\s*(\d+)",
         r"port\s*[:=]\s*['\"]?(\d+)",
         r"server\.port\s*=\s*(\d+)",
         r"run\s*\([^)]*port\s*=\s*(\d+)",
         r":(\d{4,5})",
      ]
      for path in self._iter_files(["*.py","*.js","*.ts","*.java","*.go","*.php","*.rs","*.yml","*.yaml","*.properties"],self.max_files_per_pattern_scan):
         text=self._read_text(path)
         if not text:
            continue
         for pattern in port_patterns:
            candidates.extend(int(port) for port in re.findall(pattern,text,re.IGNORECASE))

      common_preference=[8000,8080,3000,5000,5173,4200,5432,3306,27017,6379]
      for preferred in common_preference:
         if preferred in candidates:
            app_info.port=preferred
            return
      if candidates:
         app_info.port=candidates[0]

   def scan(self,manifest_file:Path,lang:str):
       app_info=ApplicationInfo()
       app_info.absolute_path=self.application_path
       app_info.manifest_file=manifest_file
       app_info.relative_path=self.application_path.relative_to(self.repo_path)
       app_info.language=lang
       self.detect_dockerfile(app_info)
       dependency_names=self._dependency_names()
       self.detect_package_manager(app_info)
       self.detect_framework(app_info,dependency_names)
       self.detect_database(app_info,dependency_names)
       self.detect_port(app_info)
       return app_info


class RepositoryScanner:
    ignored_folders = {".git", ".github", ".vscode", "__pycache__", "node_modules", "dist", "build", "target", ".venv", "venv"}
    manifests={
       "pyproject.toml":"Python",
       "requirements.txt":"Python",
       "Cargo.toml":"Rust",
       "package.json":"node.js",
       "go.mod":"Go",
       "composer.json":"PHP",
       "pom.xml":"Java"
    }



    def __init__(self, repo_path):
        self.repo_path =repo_path
    def validate(self):
     if not self.repo_path.exists():
        raise Exception("Repository does not exist")
     
    def detect_manifest(self,folder):
       for file,lang in self.manifests.items():
          manifest=folder/file
          if(manifest.exists()):
             return [file,lang]

       return None

    def iter_project_folders(self):
       for root,dirs,files in os.walk(self.repo_path):
          dirs[:]=[name for name in dirs if name not in self.ignored_folders]
          yield Path(root),set(files)
    

    def detect_Applications(self,info:ProjectInfo):
       for folder,files in self.iter_project_folders():
          for file,lang in self.manifests.items():
             if file in files:
                app_scanner=ApplicationScanner(self.repo_path,folder)
                app_info=app_scanner.scan(file,lang)
                info.apps_info.append(app_info)
                break
             
             

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
        info.project_path=self.repo_path
        self.detect_compose(info)
        self.detect_github_workflow(info)
        self.detect_Applications(info)
        return info
     
