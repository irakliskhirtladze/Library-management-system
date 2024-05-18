import pandas as pd
import random
import sqlite3
import re


def clean_data(data):
    """Clean data that from potentially unsupported characters"""
    # Define the pattern to match unsupported characters
    return re.sub(r'[^\x00-\x7F]+', '', data)


def add_random_authors():
    with open("authors.txt", "r") as f:
        authors = f.read().splitlines()
        conn = sqlite3.connect("../db.sqlite3")
        curs = conn.cursor()
        # iterate over the authors list and append them in library_author table
        for author in authors:
            author = clean_data(author)
            curs.execute("INSERT INTO library_author (full_name) VALUES (?)", (author,))
        conn.commit()
        conn.close()


def add_genres():
    with open("genres.txt", "r") as f:
        genres = f.read().splitlines()
        conn = sqlite3.connect("../db.sqlite3")
        curs = conn.cursor()
        # iterate over the genres list and append them in library_genre table
        for genre in genres:
            genre = clean_data(genre)
            curs.execute("INSERT INTO library_genre (name) VALUES (?)", (genre,))
        conn.commit()
        conn.close()


def scrape_books():
    """ Scrapes books from 'goodreads.com' and stores them to database"""

    urls = [f'https://www.goodreads.com/list/show/4893.Best_Science_Fiction_of_the_21st_Century?page={pg}' for
            pg in range(1, 12)]

    dfs = []  # Stores pandas dataframes from different webpages
    # Iterate over URLs and get books from them using pandas
    for url in urls:
        df = pd.read_html(url)[0]
        df['title'] = df[2].apply(lambda x: x.split('by')[0])

        quantity = [random.randint(10, 1000) for _ in range(len(df))]
        df['quantity'] = quantity
        author_id = [random.randint(1, 103) for _ in range(len(df))]
        df['author_id'] = author_id
        genre_id = [random.randint(1, 10) for _ in range(len(df))]
        df['genre_id'] = genre_id
        year = [random.randint(1849, 2021) for _ in range(len(df))]
        df['year'] = year

        # Clean book titles
        df['title'] = df['title'].apply(lambda x: clean_data(x))
        df['title'] = df['title'].apply(lambda x: x.strip())

        # print(df)
        dfs.append(df)

    # Concatenate dataframes into single dataframe and save to database
    full_df = pd.concat(dfs, axis=0)
    full_df.drop([0, 1, 2, 3], axis=1, inplace=True)

    conn = sqlite3.connect("../db.sqlite3")
    curs = conn.cursor()
    # iterate over the authors list and append them in library_author table
    for _, book in full_df.iterrows():
        curs.execute("INSERT INTO library_book (title, release_year, quantity, author_id, genre_id) VALUES (?,?,?,?,?)",
                     (book['title'], book['year'], book['quantity'], book['author_id'], book['genre_id']))
    conn.commit()
    conn.close()


add_random_authors()
add_genres()
scrape_books()
