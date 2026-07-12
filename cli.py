import typer
from pathlib import Path

from main import run_agent

app = typer.Typer()

@app.command()
def version():
    print("0.1.0")
    
    
@app.command()
def init():

    repo = Path.cwd()

    run_agent(repo)

if __name__ == "__main__":
    app()