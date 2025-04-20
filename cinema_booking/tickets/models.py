from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import uuid
import qrcode
from django.core.files.base import ContentFile
import io

# Phim
class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.CharField(max_length=50)
    director = models.CharField(max_length=100)
    duration = models.IntegerField()  # Thời lượng (phút)
    poster_url = models.URLField()
    trailer_url = models.URLField(blank=True, null=True)
    release_date = models.DateField()
    language =models.CharField(max_length=50, null=True, blank=True)
    actor =  models.CharField(max_length=200, null=True, blank=True)
    def __str__(self):
        return self.title

# Rạp chiếu phim
class Theater(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15)

    def get_province(self):
        """Extract province/city from theater address"""
        # Split address by comma and get the last part
        parts = self.address.split(',')
        if len(parts) > 1:
            return parts[-1].strip()
        return 'Khác'

    def __str__(self):
        return self.name

# Loại ghế
class SeatType(models.Model):
    name = models.CharField(max_length=50)
    price_multiplier = models.FloatField(default=1.0)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} (x{self.price_multiplier})"

# Ghế
class Seat(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='seats')
    row = models.IntegerField()
    column = models.IntegerField()
    seat_type = models.ForeignKey(SeatType, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['room', 'row', 'column']
        ordering = ['row', 'column']

    def __str__(self):
        return f"R{self.row}C{self.column} - {self.room}"

# Phòng chiếu
class Room(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    room_number = models.CharField(max_length=10)
    total_seats = models.IntegerField()
    rows = models.IntegerField()
    columns = models.IntegerField()
    
    def __str__(self):
        return f"{self.theater.name} - Phòng {self.room_number}"
        
    def get_seats(self):
        """Lấy thông tin tất cả ghế trong phòng"""
        return self.seats.filter(is_active=True).order_by('row', 'column')

    def calculate_rows_columns(self):
        """Tính toán số hàng và cột dựa trên tổng số ghế"""
        # Tính số cột (chiều ngang) - thường là số chẵn
        columns = round(((self.total_seats / 10) ** 0.5) * 2)  # Nhân 2 để có tỷ lệ 2:1
        if columns % 2 != 0:  # Đảm bảo số cột là số chẵn
            columns += 1
        
        # Tính số hàng cần thiết
        rows = (self.total_seats + columns - 1) // columns  # Làm tròn lên
        
        return rows, columns

    def create_seats(self):
        """Tạo tự động các ghế cho phòng"""
        # Xóa các ghế cũ nếu có
        self.seats.all().delete()
        
        # Tính toán số hàng và cột
        rows, columns = self.calculate_rows_columns()
        self.rows = rows
        self.columns = columns
        
        # Tạo ghế mới
        default_seat_type = SeatType.objects.get_or_create(
            name='Standard',
            defaults={'price_multiplier': 1.0}
        )[0]
        
        seats = []
        seats_created = 0
        
        for row in range(1, rows + 1):
            for col in range(1, columns + 1):
                if seats_created < self.total_seats:
                    seats.append(Seat(
                        room=self,
                        row=row,
                        column=col,
                        seat_type=default_seat_type,
                        is_active=True
                    ))
                    seats_created += 1
                else:
                    # Nếu đã đủ số ghế, những ghế còn lại sẽ không active
                    seats.append(Seat(
                        room=self,
                        row=row,
                        column=col,
                        seat_type=default_seat_type,
                        is_active=False
                    ))
        
        Seat.objects.bulk_create(seats)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new or self.total_seats != self.__class__.objects.get(pk=self.pk).total_seats if self.pk else True:
            # Tính toán số hàng và cột mới
            self.rows, self.columns = self.calculate_rows_columns()
        super().save(*args, **kwargs)
        if is_new or self.total_seats != self.__class__.objects.get(pk=self.pk).total_seats if self.pk else True:
            self.create_seats()

# Lịch chiếu
class Showtime(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    show_date = models.DateField()  # Ngày chiếu
    start_time = models.TimeField()  # Giờ bắt đầu
    end_time = models.TimeField(blank=True, null=True)  # Giờ kết thúc (tính tự động)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reserved_seats = models.JSONField(default=list, blank=True)
    
    def is_seat_available(self, seat_id):
        """Kiểm tra ghế có còn trống không"""
        return seat_id not in self.reserved_seats
    
    def get_available_seats(self):
        """Lấy danh sách ghế còn trống"""
        all_seats = self.room.get_seats()
        return [seat for seat in all_seats if seat.id not in self.reserved_seats]    

    def get_start_datetime(self):
        """Kết hợp show_date và start_time thành DateTime."""
        return datetime.combine(self.show_date, self.start_time)

    def calculate_end_time(self):
        """Tính thời gian kết thúc dựa trên start_time và duration."""
        start_datetime = self.get_start_datetime()
        duration = self.movie.duration  # Thời lượng phim (phút)
        end_datetime = start_datetime + timedelta(minutes=duration)
        return end_datetime.time()  # Chỉ lấy phần thời gian (TimeField)

    def clean(self):
        """Kiểm tra trùng lịch chiếu trong cùng phòng."""
        if not self.end_time:
            self.end_time = self.calculate_end_time()

        start_datetime = self.get_start_datetime()
        end_datetime = datetime.combine(self.show_date, self.end_time)

        # Tìm các suất chiếu khác trong cùng phòng và cùng ngày
        overlapping_showtimes = Showtime.objects.filter(
            room=self.room,
            show_date=self.show_date,
        ).exclude(id=self.id)

        # Kiểm tra xem có suất chiếu nào giao nhau về thời gian không
        for showtime in overlapping_showtimes:
            other_start = showtime.get_start_datetime()
            other_end = datetime.combine(showtime.show_date, showtime.end_time)
            if (other_start < end_datetime) and (other_end > start_datetime):
                raise ValidationError("This room is already booked for the selected time slot.")

    def save(self, *args, **kwargs):
        # Tính end_time trước khi lưu
        if not self.end_time:
            self.end_time = self.calculate_end_time()
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.movie.title} - {self.show_date} {self.start_time}"

# Vé
class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, paid, used
    purchase_date = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)  # Lưu ảnh QR

    def generate_qr_data(self):
        """Tạo dữ liệu cho mã QR dựa trên thông tin vé."""
        qr_data = f"Ticket-{self.id}-{self.user.username}-{self.showtime.id}-{self.seat.id}"
        if not self.id:  # Nếu chưa có ID (trước khi lưu lần đầu)
            qr_data = f"Ticket-{uuid.uuid4()}-{self.user.username}-{self.showtime.id}-{self.seat.id}"
        return qr_data

    def create_qr_image(self):
        """Tạo và lưu ảnh QR vào qr_code."""
        qr_data = self.generate_qr_data()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')

        # Chuyển ảnh QR thành file để lưu vào ImageField
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"ticket_{self.id or uuid.uuid4()}.png"
        self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
        buffer.close()

    def save(self, *args, **kwargs):
        # Nếu chưa có qr_code hoặc chưa có ID (lần lưu đầu tiên), tạo ảnh QR
        if not self.qr_code:
            super().save(*args, **kwargs)  # Lưu trước để có ID
            self.create_qr_image()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vé {self.seat} - {self.showtime}"

# Giao dịch (tùy chọn)
class Transaction(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Tự động tạo transaction_id nếu chưa có
        if not self.transaction_id:
            # Tạo transaction_id duy nhất dựa trên timestamp và uuid
            self.transaction_id = f"TXN-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Giao dịch {self.transaction_id} - {self.user.username}"
