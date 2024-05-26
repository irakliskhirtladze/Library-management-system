import pandas as pd
import random
import re
import os
import django
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from Library_management_project.settings import BASE_DIR
from library.models import Author, Genre, Book

# Ensure the settings module is set up correctly
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
django.setup()


def clean_data(data):
    """Clean data that from potentially unsupported characters"""
    # Define the pattern to match unsupported characters
    return re.sub(r'[^\x00-\x7F]+', '', data)


def add_random_authors():
    try:
        authors_file = os.path.join(BASE_DIR, "insert_data", "authors.txt")
        with open(authors_file, "r") as f:
            authors = f.read().splitlines()
        for author in authors:
            author = clean_data(author)
            Author.objects.create(full_name=author)
    except Exception as e:
        print(f'Error adding authors: {e}')


def add_genres():
    try:
        genres_file = os.path.join(BASE_DIR, "insert_data", "genres.txt")
        with open(genres_file, "r") as f:
            genres = f.read().splitlines()
        for genre in genres:
            genre = clean_data(genre)
            Genre.objects.create(name=genre)
    except Exception as e:
        print(f'Error adding genres: {e}')


def scrape_books():
    """ Scrapes books from 'goodreads.com' and stores them to database"""
    try:
        urls = [f'https://www.goodreads.com/list/show/4893.Best_Science_Fiction_of_the_21st_Century?page={pg}' for
                pg in range(1, 12)]

        dfs = []  # Stores pandas dataframes from different webpages
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # Iterate over URLs and scrape books from them using pandas
        for url in urls:
            df = pd.read_html(url)[0]
            df['title'] = df[2].apply(lambda x: x.split('by')[0])

            df['quantity'] = [random.randint(10, 1000) for _ in range(len(df))]
            df['author_id'] = [random.randint(1, 103) for _ in range(len(df))]
            df['genre_id'] = [random.randint(1, 10) for _ in range(len(df))]
            df['year'] = [random.randint(1849, 2021) for _ in range(len(df))]

            # Clean book titles
            df['title'] = df['title'].apply(lambda x: clean_data(x))
            df['title'] = df['title'].apply(lambda x: x.strip())

            dfs.append(df)

        # Concatenate dataframes into single dataframe and save to database
        full_df = pd.concat(dfs, axis=0)
        full_df.drop([0, 1, 2, 3], axis=1, inplace=True)

        # iterate over the authors list and append them in library_author table
        for _, book in full_df.iterrows():
            Book.objects.create(
                title=book['title'],
                release_year=book['year'],
                quantity=book['quantity'],
                author_id=book['author_id'],
                genre_id=book['genre_id']
            )

    except Exception as e:
        print(f'Error scraping books: {e}')
