from scanner.scanner import RepositoryScanner

scanner = RepositoryScanner("../interview_app")

info=scanner.scan()
print(info.project_name)
print("has compose=",info.has_compose)
print("has github workflows=",info.has_github_workflow)
for app in info.apps_info:
    print("Application Info")
    print("\t Application path=",app.application_path)
    print("\t language=",app.language)
    print("\t framwork=",app.framework)
    print("\t package_manager=",app.package_manager)
    print("\t databse",app.databse)
    print("\t has dockerfile:",app.has_dockerfile)