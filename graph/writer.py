from graph.state import State
from pathlib import Path
def write(state:State)->State:
    for gen_file in state['generated_files']:
        file:Path=gen_file["file"]
        content=gen_file["content"]
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(content)
        print(f"Generated {file.name} {file.as_posix()}")

    return state