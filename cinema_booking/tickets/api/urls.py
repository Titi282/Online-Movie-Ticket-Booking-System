from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'movies', views.MovieViewSet)
router.register(r'theaters', views.TheaterViewSet)
router.register(r'seat-types', views.SeatTypeViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'seats', views.SeatViewSet)
router.register(r'showtimes', views.ShowtimeViewSet)
router.register(r'tickets', views.TicketViewSet)
router.register(r'transactions', views.TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]