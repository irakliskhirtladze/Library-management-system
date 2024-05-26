from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import requests
from django.conf import settings

from web.utils import fetch_all_pages


@login_required
def home(request):
    page = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    author = request.GET.get('author', '')
    genre = request.GET.get('genre', '')

    api_url = f"{settings.API_URL}/library/books/"
    params = {
        'page': page,
        'search': search,
        'author': author,
        'genre': genre,
    }

    # Create a session object to maintain the authentication session
    session = requests.Session()
    session.cookies.update(request.COOKIES)
    csrf_token = get_token(request)
    response = session.get(api_url, headers={'X-CSRFToken': csrf_token}, params=params)

    if response.status_code == 200:
        data = response.json()
        books = data.get('results', [])
        pagination = {
            'count': data.get('count', 0),
            'next': data.get('next'),
            'previous': data.get('previous'),
            'page': int(page),
            'total_pages': (data.get('count', 0) + 4) // 5,  # Assuming 5 books per page
        }
    else:
        books = []
        pagination = {
            'count': 0,
            'next': None,
            'previous': None,
            'page': int(page),
            'total_pages': 1,
        }

    # Fetch all authors and genres for filtering options
    authors = []
    genres = []

    try:
        # Fetch authors from API and format as (id, full_name) tuples
        authors_data = fetch_all_pages(session, f"{settings.API_URL}/library/authors/", {'X-CSRFToken': csrf_token})
        authors = [(author['id'], author['full_name']) for author in authors_data]
    except Exception as e:
        print(f"Error fetching authors: {e}")

    try:
        # Fetch genres from API and format as (id, name) tuples
        genres_data = fetch_all_pages(session, f"{settings.API_URL}/library/genres/", {'X-CSRFToken': csrf_token})
        genres = [(genre['id'], genre['name']) for genre in genres_data]
    except Exception as e:
        print(f"Error fetching genres: {e}")

    context = {
        'books': books,
        'pagination': pagination,
        'search': search,
        'author': author,
        'genre': genre,
        'authors': authors,
        'genres': genres,
    }
    return render(request, 'index.html', context)


@login_required
def book_detail(request, pk):
    api_url = f"{settings.API_URL}/library/books/{pk}/"

    # Create a session object to maintain the authentication session
    session = requests.Session()

    # Get the session cookies and CSRF token from the current request
    session.cookies.update(request.COOKIES)
    csrf_token = get_token(request)

    if request.method == 'POST':
        if 'reserve' in request.POST:
            reserve_api_url = f"{api_url}reserve/"
            response = session.post(reserve_api_url, headers={'X-CSRFToken': csrf_token})
            if response.status_code == 201:
                return redirect('book_detail', pk=pk)
            else:
                error_message = response.json().get('detail', 'Reservation failed.')
                print(f"Reservation Error: {error_message}")

        if 'cancel_reservation' in request.POST:
            cancel_reservation_api_url = f"{api_url}cancel_reservation/"
            response = session.post(cancel_reservation_api_url, headers={'X-CSRFToken': csrf_token})
            if response.status_code == 200:
                return redirect('book_detail', pk=pk)
            else:
                error_message = response.json().get('detail', 'Canceling reservation failed.')
                print(f"Cancel Reservation Error: {error_message}")

    response = session.get(api_url, headers={'X-CSRFToken': csrf_token})

    if response.status_code == 200:
        book = response.json()
        book['is_available'] = book['quantity'] > (book['currently_borrowed_count'] + book['active_reservations_count'])

        # Check if the current user has an active reservation for this book
        reservation_api_url = f"{settings.API_URL}/library/books/{pk}/cancel_reservation/"
        reservation_check_response = session.get(reservation_api_url, headers={'X-CSRFToken': csrf_token})

        if reservation_check_response.status_code == 200:
            reservations = reservation_check_response.json().get('results', [])
            book['user_has_reservation'] = any(reservation['user'] == request.user.id for reservation in reservations)
        else:
            book['user_has_reservation'] = False
    else:
        book = {}

    context = {
        'book': book,
    }
    return render(request, 'web/book_detail.html', context)
