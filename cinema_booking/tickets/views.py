from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.views import View
from django.contrib.auth.models import User
from .models import Movie, Theater, Room, Showtime, Ticket, Transaction, Seat, SeatType
from .serializers import (UserSerializer, MovieSerializer, TheaterSerializer,
                         RoomSerializer, ShowtimeSerializer, TicketSerializer,
                         TransactionSerializer)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from datetime import datetime, timedelta
from django.db.models import Q
from collections import defaultdict
import re
import json
from django.http import JsonResponse
from django.http import HttpResponse

def extract_province(theater_name):
    if ',' in theater_name:
        return theater_name.split(',')[-1].strip()
    return 'Khác'

def auth_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'login':
            username = request.POST.get('sign-in-email')
            password = request.POST.get('sign-in-passwd')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Đăng nhập thành công!')
                return redirect('home')
            else:
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
        elif form_type == 'signup':
            first_name = request.POST.get('sign-up-name')
            email = request.POST.get('sign-up-email')
            password = request.POST.get('sign-up-passwd')
            password2 = request.POST.get('sign-up-passwd2')
            if not all([first_name, email, password, password2]):
                messages.error(request, 'Vui lòng điền đầy đủ thông tin')
            elif password != password2:
                messages.error(request, 'Mật khẩu xác nhận không khớp')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email đã được sử dụng')
            elif len(password) < 8:
                messages.error(request, 'Mật khẩu phải dài ít nhất 8 ký tự')
            else:
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name
                    )
                    login(request, user)
                    messages.success(request, 'Đăng ký thành công!')
                    return redirect('home')
                except Exception as e:
                    messages.error(request, f'Đã xảy ra lỗi: {str(e)}')
    messages_list = [
        {"message": message.message, "level": message.tags}
        for message in messages.get_messages(request)
    ]
    return render(request, 'sign_in.html', {"messages": json.dumps(messages_list)})

def logout_view(request):
    logout(request)
    messages.success(request, 'Đã đăng xuất thành công!')
    return redirect('login')

def home_view(request):
    try:
        movies = Movie.objects.all()
        theaters = Theater.objects.all()
        for movie in movies:
            if movie.trailer_url and "youtube.com/embed/" in movie.trailer_url:
                video_id = movie.trailer_url.split("embed/")[-1].split("?")[0]
                movie.trailer_url = f"https://www.youtube.com/embed/{video_id}"
    except Exception as e:
        movies = []
        theaters = []
        print(f"Error loading movies: {str(e)}")
    
    return render(request, 'index.html', {
        'movies': movies,
        'theaters': theaters
    })

def movies_view(request):
    movies = Movie.objects.all()
    movies_latest = Movie.objects.order_by('-release_date')
    movies_adults = Movie.objects.filter(
        Q(genre__icontains='Hoạt hình') | Q(genre__icontains='Phiêu lưu')
    ).order_by('-release_date')
    
    theaters = Theater.objects.all()
    selected_theater = None
    
    # Get the selected theater if it exists in session
    if 'selected_theater' in request.session:
        try:
            selected_theater = Theater.objects.get(id=request.session['selected_theater'])
        except Theater.DoesNotExist:
            # If theater doesn't exist, remove it from session
            del request.session['selected_theater']
    
    for movie in movies:
        if "youtube.com/embed/" in movie.trailer_url:
            video_id = movie.trailer_url.split("embed/")[-1].split("?")[0]
            movie.trailer_url = f"https://www.youtube.com/embed/{video_id}"
    return render(request, 'movies.html', {
        'movies': movies, 
        'movies_latest': movies_latest, 
        'movies_adults': movies_adults,
        'selected_theater': selected_theater,
        'theaters': theaters
    })

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    movie.trailer_url = movie.trailer_url.replace("watch?v=", "embed/")
    
    showtimes = Showtime.objects.filter(movie=movie)
    theaters = Theater.objects.all()
    theaters_by_province = defaultdict(list)
    for theater in theaters:
        province = extract_province(theater.name)
        theaters_by_province[province].append(theater)
    
    # Get selected theater if exists
    selected_theater = None
    if 'selected_theater' in request.session:
        try:
            selected_theater = Theater.objects.get(id=request.session['selected_theater'])
        except Theater.DoesNotExist:
            del request.session['selected_theater']
    
    context = {
        'movie': movie,
        'showtimes': showtimes,
        'theaters_by_province': dict(theaters_by_province),
        'current_date': datetime.now(),
        'selected_theater': selected_theater,
    }
    return render(request, 'movie_detail.html', context)

def about_view(request):
    return render(request, 'about.html')

def ticket_view(request):
    return render(request, 'e-ticket.html')

def ticket_booking_view(request, movie_id, cinema):
    movie = get_object_or_404(Movie, id=movie_id)
    theater = get_object_or_404(Theater, id=cinema)
    today = datetime.today().date()
    days = [
        {
            'id': i + 1,
            'numeric': (today + timedelta(days=i)).strftime('%d/%m'),
            'day_name': (today + timedelta(days=i)).strftime('%A')[:3],
            'iso_date': (today + timedelta(days=i)).isoformat()
        }
        for i in range(7)
    ]
    selected_date_str = request.GET.get('date', today.isoformat())
    try:
        selected_date = datetime.fromisoformat(selected_date_str).date()
    except ValueError:
        selected_date = today
    showtimes = Showtime.objects.filter(
        movie_id=movie.id,
        room__theater=theater,
        show_date=selected_date
    ).select_related('room', 'room__theater')
    showtimes_by_room = defaultdict(list)
    for showtime in showtimes:
        showtimes_by_room[showtime.room].append(showtime)
    context = {
        'days': days,
        'showtimes_by_room': dict(showtimes_by_room),
        'movie_id': movie_id,
        'movie': movie,
        'theater': theater,
        'selected_date': selected_date.isoformat(),
    }
    return render(request, 'ticket-booking.html', context)

def seat_sel_view(request, showtime_id):
    try:
        showtime = get_object_or_404(Showtime, id=showtime_id)
        # Get all seats for the room
        seats = Seat.objects.filter(room=showtime.room).select_related('seat_type')
        # Get all seat types
        seat_types = SeatType.objects.all()
        
        context = {
            'showtime': showtime,
            'seats': seats,
            'seat_types': seat_types,
        }
        return render(request, 'seat_selection/seat_sel.html', context)
    except Showtime.DoesNotExist:
        return HttpResponse("Invalid showtime")

def select_theater(request):
    if request.method == 'POST':
        theater_id = request.POST.get('theater')
        if theater_id:
            request.session['selected_theater'] = theater_id
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})