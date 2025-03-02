import typer
import pandas as pandas

app = typer.Typer()

@app.command()
def clean():
    pass


if __name__ == "__main__":
    app()