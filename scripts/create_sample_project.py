"""Generate an empty local project without embedding private source images."""
from pathlib import Path
from goshman.project import create_project
if __name__=="__main__":
    print(create_project(Path('projects/demo_crocodile'), 'Animatronic Crocodile Cowboy'))
