import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Waits for the database to be ready'

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        connected = False
        while not connected:
            try:
                connection.ensure_connection()
                connected = True
            except OperationalError as e:
                self.stdout.write(f'Database unavailable: {e}')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))