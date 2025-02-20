from alive_progress import alive_bar
import time
# from .app_deepseek import TaskManagerApp
from . import app_main

__all__ = ["app"]

def main() -> None:
    with alive_bar(500) as bar:
        for _ in range(500) :
            time.sleep(.001)
            bar()   

    app_main.run_app()
