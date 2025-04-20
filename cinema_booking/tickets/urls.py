from django.contrib import admin
from django.urls import path, include
from .views import (home_view, auth_view, logout_view, movies_view, about_view, 
                   ticket_view, ticket_booking_view, seat_sel_view, movie_detail,
                   select_theater)

urlpatterns = [
    path('logout/', logout_view, name='logout'),
    path('login/', auth_view, name='login'),
    path('movies/', movies_view, name='movies'),
    path('chi-tiet-phim-<int:movie_id>/', movie_detail, name='movie_detail'),
    path('about/', about_view, name='about'),
    path('ticket/', ticket_view, name='ticket'),
    path('select-theater/', select_theater, name='select_theater'),
    path('ticketbooking/<str:cinema>/<int:movie_id>/', ticket_booking_view, name='ticketbooking'),
    path('seat_sel/<int:showtime_id>/', seat_sel_view, name='seat_sel'),
    path('', home_view, name='home'),
]
    