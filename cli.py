import typer
from pathlib import Path



app = typer.Typer()

@app.command()
def version():
    print("0.1.0")
    
    
@app.command()
def init():
    print("initialising AI agents...")
    from main import run_agent
    repo = Path.cwd()
    print("scanning repository...")
    run_agent(repo)

if __name__ == "__main__":
    app()