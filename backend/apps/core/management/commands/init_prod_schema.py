"""
FoodShare — Management Command: init_prod_schema
Creates the 'foodshare' schema in the PostgreSQL database before migrations run.
Usage (in production EC2 deployment):
    python manage.py init_prod_schema
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Creates the 'foodshare' PostgreSQL schema if it does not already exist."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS foodshare;")
            self.stdout.write(
                self.style.SUCCESS("PostgreSQL schema 'foodshare' successfully created or already exists.")
            )

