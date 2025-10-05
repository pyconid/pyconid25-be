import typer

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def send_test_email(email: str, name: str):
    from core.email import try_send_email
    import asyncio

    asyncio.run(try_send_email(recipient=email, name=name))


if __name__ == "__main__":
    app()
