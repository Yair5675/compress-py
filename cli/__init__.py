import typer
from .huffman import huffman_app

# The name of the app:
APP_NAME = "compress-py"

# The main app that will contain all algorithms:
main_app = typer.Typer(name=APP_NAME, no_args_is_help=True, rich_markup_mode="rich", add_completion=False)
main_app.add_typer(huffman_app)
