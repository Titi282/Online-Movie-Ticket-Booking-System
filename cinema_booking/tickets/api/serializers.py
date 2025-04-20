# Định nghĩa serializers - Chuyển đổi dữ liệu giữa model và JSON cho API
from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Movie, Theater, Room, Showtime, Ticket, Transaction, Seat, SeatType

# Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id']

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'genre', 'director', 'duration',
                 'poster_url', 'trailer_url', 'release_date', 'language', 'actor']
        read_only_fields = ['id']

class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = ['id', 'name', 'address', 'phone']
        read_only_fields = ['id']

class SeatTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatType
        fields = ['id', 'name', 'price_multiplier', 'description']
        read_only_fields = ['id']

class RoomSerializer(serializers.ModelSerializer):
    theater = TheaterSerializer(read_only=True)
    theater_id = serializers.PrimaryKeyRelatedField(
        queryset=Theater.objects.all(), source='theater', write_only=True
    )

    class Meta:
        model = Room
        fields = ['id', 'theater', 'theater_id', 'room_number', 'rows', 'columns', 'total_seats']
        read_only_fields = ['id']

class SeatSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), source='room', write_only=True
    )
    seat_type = SeatTypeSerializer(read_only=True)
    seat_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SeatType.objects.all(), source='seat_type', write_only=True
    )

    class Meta:
        model = Seat
        fields = ['id', 'room', 'room_id', 'row', 'column', 'seat_type', 'seat_type_id', 'active']
        read_only_fields = ['id']

class ShowtimeSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(), source='movie', write_only=True
    )
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), source='room', write_only=True
    )

    class Meta:
        model = Showtime
        fields = ['id', 'movie', 'movie_id', 'room', 'room_id', 'show_date',
                 'start_time', 'end_time', 'price', 'reserved_seats']
        read_only_fields = ['id', 'end_time']

class TicketSerializer(serializers.ModelSerializer):
    showtime = ShowtimeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    seat = SeatSerializer(read_only=True)
    showtime_id = serializers.PrimaryKeyRelatedField(
        queryset=Showtime.objects.all(), source='showtime', write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    seat_id = serializers.PrimaryKeyRelatedField(
        queryset=Seat.objects.all(), source='seat', write_only=True
    )

    class Meta:
        model = Ticket
        fields = ['id', 'user', 'user_id', 'showtime', 'showtime_id', 'seat', 'seat_id',
                 'price', 'status', 'purchase_date', 'qr_code']
        read_only_fields = ['id', 'purchase_date', 'qr_code']

    def validate(self, data):
        # Check if seat is already booked for this showtime
        showtime = data['showtime']
        seat = data['seat']
        if Ticket.objects.filter(showtime=showtime, seat=seat, status__in=['pending', 'paid']).exists():
            raise serializers.ValidationError("This seat is already booked.")
        return data

class TransactionSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    ticket_id = serializers.PrimaryKeyRelatedField(
        queryset=Ticket.objects.all(), source='ticket', write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'user_id', 'ticket', 'ticket_id', 'amount',
                 'payment_method', 'transaction_date', 'status', 'transaction_id']
        read_only_fields = ['id', 'transaction_date', 'transaction_id']