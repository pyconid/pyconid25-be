import typer

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def initial_data():
    from seeders.initial_seeders import initial_seeders

    initial_seeders()


@app.command()
def send_test_email(email: str, name: str):
    from core.email import try_send_email
    import asyncio

    asyncio.run(try_send_email(recipient=email, name=name))


@app.command()
def download_location_data():
    from scripts.download_location_data import download_location_data

    download_location_data()


@app.command()
def import_location_data():
    from seeders.initial_country_city_state import initial_country_city_state_seeders
    from models import factory_session

    with factory_session() as session:
        initial_country_city_state_seeders(db=session, is_commit=True)


@app.command()
def clear_location_data():
    from models import factory_session
    from seeders.initial_country_city_state import clear_data_location

    with factory_session() as session:
        clear_data_location(db=session, is_commit=True)


if __name__ == "__main__":
    app()
