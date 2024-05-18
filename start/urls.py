from django.urls import path
from start.views import home


urlpatterns = [
    path('', home, name='home'),
]
