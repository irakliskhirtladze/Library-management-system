from django.core.management.base import BaseCommand
from insert_data.data import add_random_authors, add_genres, scrape_books


class Command(BaseCommand):
    help = 'Populates the database with initial data by running data.py'

    def handle(self, *args, **kwargs):
        try:
            add_random_authors()
            add_genres()
            scrape_books()
            self.stdout.write(self.style.SUCCESS('Successfully populated the database'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error populating the database: {e}'))
