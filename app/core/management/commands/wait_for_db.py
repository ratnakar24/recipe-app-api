from django.core.management import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import time


class Command(BaseCommand):
    """Django command to pause execution until databse cis available"""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for databse...")
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections['default']
            except OperationalError:
                self.stdout.write("Database unavailable,\
                    waiting for 1 second..")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!!"))
