# app/seed/cli.py
import click
from flask import Blueprint

from .seed_hub_data import seed_hub_data

seed_blp = Blueprint("seed", __name__)

@seed_blp.cli.command("seed-hub")
@click.option("--clear", is_flag=True, help="Clear hub tables before seeding")
def seed_hub(clear: bool):
    """
    Seed mock hub data (banks, loan rates, legal resources).
    Usage:
      flask --app run.py seed-hub
      flask --app run.py seed-hub --clear
    """
    result = seed_hub_data(clear_first=clear)
    click.echo(f"Seed completed: {result}")
