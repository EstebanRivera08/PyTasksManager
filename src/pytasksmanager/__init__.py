from alive_progress import alive_bar
import time
from . import app

__all__ = ["app"]

def main() -> None:
    print("Hello from pytasksmanager!")

    with alive_bar(500) as bar:
        for _ in range(500) :
            time.sleep(.001)
            bar()    

    app.run_app()

