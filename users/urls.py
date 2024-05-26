from django.urls import path
from users.views import SignUpView, LogInView, log_out


urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LogInView.as_view(), name='login'),
    path('logout/', log_out, name='logout'),
]
