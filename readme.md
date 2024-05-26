# Library manager system

## Description
Library management system is built with Django and Rest framework. It's intended to manage a book library and 
allow users to register, view, reserve and make a wish for currently unavailable books.

Librarians can use admin panel, and to some extent API to manage books, genres, authors and see library statistics.

## Project Structure
Project has 2 main apps: users and library. There's also Third app called start, which is just used to render some
homepage templates and make it a bit easier to navigate.

### Users app
This app is used to define a custom user model and allow registration/login for users.


### Library app
This app is built with Rest framework, and it's based on few key models: Genre, Author, Book, Reservation and Borrow
models.

Genre and Author are very simple models related to Book model.

Book model has more complicated structure, with several dynamic fields and methods.
Same is true for Reservation and Borrow models.

### Web app
This app allows limited frontend capabilities with template rendering. Uses only HTML and CSS to do so.

### Business logic
The business logic is centered (at least I tried) around models to allow robustness and reduce code duplication.

For example: A user cannot reserve a book if that user has another active reservation, has unreturned borrowing 
or the book is unavailable. Instead of validating this logic separately for API view and for admin panel,
I included the validation in model class.
This allows a single validation which can be used in several places.

Other rules include:
- User cannot borrow book if they have an unreturned book or if book is unavailable (meaning all of its copies are
reserved or borrowed).
- When user borrows a book, if they have active reservation, it will be automatically canceled.
- User can make a wish for a book only if the book is unavailable at the moment.

## Setup Instructions

1. Clone the repository:
```
git clone https://github.com/irakliskhirtladze/Library-management-system.git
```
2. Create a virtual environment and activate it. To install dependencies run the command:
```
pip install -r requirements.txt
```
3. Apply migrations:
```
python manage.py migrate
```
4. Populate the database with initial data (random book names, authors and genres):
```
python manage.py populate_db
```
5. To create admin user run the command below and then follow the instructions:
```
python manage.py createsuperuser
```
7. Run the development server:
``` 
python manage.py runserver
```

Finally go to http://127.0.0.1:8000/ or http://127.0.0.1:8000/admin to start using the project.


## Task automation
If you want to also automate tasks for periodic execution, launch redis, 
and then in separate terminals run the following commands, one in each:

```
celery -A Library_management_project worker --loglevel=info
```
```
celery -A Library_management_project beat --loglevel=info
```
