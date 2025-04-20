from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Movie, Theater, Room, Showtime, Ticket, Transaction, SeatType, Seat

# Unregister the default User admin
admin.site.unregister(User)

# Register User with custom admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'genre', 'director', 'release_date', 'actor', 'language')
    search_fields = ('title', 'director', 'actor', 'language', 'genre')

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'phone')
    search_fields = ('name',)

@admin.register(SeatType)
class SeatTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price_multiplier', 'description')
    search_fields = ('name',)

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'row', 'column', 'seat_type', 'is_active')
    list_filter = ('room', 'seat_type', 'is_active')
    search_fields = ('room__room_number',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'theater', 'room_number', 'total_seats', 'rows', 'columns')
    list_filter = ('theater',)
    search_fields = ('room_number',)

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie', 'room', 'show_date', 'start_time', 'end_time', 'price')
    list_filter = ('show_date', 'room', 'movie')
    search_fields = ('movie__title', 'room__room_number')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'showtime', 'seat', 'price', 'status', 'purchase_date')
    list_filter = ('status', 'showtime__show_date')
    search_fields = ('user__username', 'showtime__movie__title', 'seat__id')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ticket', 'amount', 'payment_method', 'status', 'transaction_date')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__username', 'transaction_id')
