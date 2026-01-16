import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from app_quan_ly.models import SanPham, KhachHang
from unidecode import unidecode
import random

# Lấy user admin
user = User.objects.first()
if not user:
    print("❌ Không tìm thấy user. Tạo superuser trước!")
    exit()

print(f"📌 Sử dụng user: {user.username}")

# Danh sách tên sản phẩm mẫu
product_templates = [
    'Coca Cola', 'Pepsi', 'Sting', 'Redbull', 'Number 1', '7Up', 'Aquafina',
    'Lavie', 'Revive', 'Lipton', 'Trà xanh', 'Trà đào', 'Sữa tươi', 'Sữa chua',
    'Bánh mì', 'Bánh bao', 'Xôi', 'Cơm', 'Phở', 'Bún', 'Mì', 'Hủ tiếu',
    'Snack', 'Kẹo', 'Socola', 'Bánh quy', 'Mứt', 'Nước mắm', 'Dầu ăn',
    'Gạo', 'Đường', 'Muối', 'Tương ớt', 'Nước tương', 'Giấm', 'Bia',
    'Rượu', 'Thuốc lá', 'Bật lửa', 'Diêm', 'Pin', 'Bóng đèn', 'Dây điện'
]

don_vi = ['Chai', 'Lon', 'Hộp', 'Gói', 'Cái', 'Bộ', 'Thùng', 'Kg', 'Lít', 'Túi']
sizes = ['330ml', '500ml', '1L', '1.5L', '2L', 'Nhỏ', 'Vừa', 'Lớn', 'XL', 'XXL']
brands = ['Vinamilk', 'TH True Milk', 'Dutch Lady', 'Milo', 'Nestlé', 'Unilever', 
          'P&G', 'Coca-Cola', 'Pepsi', 'Suntory', 'Acecook', 'Vifon']

# Tạo 4000 sản phẩm
print("🔄 Đang tạo 4000 sản phẩm...")
products_created = 0

for i in range(4000):
    template = random.choice(product_templates)
    brand = random.choice(brands) if random.random() > 0.5 else ''
    size = random.choice(sizes) if random.random() > 0.6 else ''
    
    # Tạo tên sản phẩm
    parts = [p for p in [brand, template, size] if p]
    tensanpham = ' '.join(parts)
    
    # Tạo tên không dấu
    tensanphamkhongdau = unidecode(tensanpham).lower()
    
    donvitinh = random.choice(don_vi)
    
    # Kiểm tra trùng
    if SanPham.objects.filter(tensanphamkhongdau=tensanphamkhongdau, donvitinh=donvitinh).exists():
        continue
    
    dongiagoc = random.randint(5, 200) * 1000
    dongiaban = int(dongiagoc * random.uniform(1.2, 2.0))
    tonkho = random.randint(0, 500)
    
    # Tạo barcode ngẫu nhiên
    barcode = f"893{random.randint(1000000000, 9999999999)}" if random.random() > 0.3 else ''
    
    SanPham.objects.create(
        tensanpham=tensanpham,
        tensanphamkhongdau=tensanphamkhongdau,
        donvitinh=donvitinh,
        dongiagoc=dongiagoc,
        dongiaban=dongiaban,
        tonkho=tonkho,
        barcode=barcode,
        user=user
    )
    products_created += 1
    
    if (i + 1) % 500 == 0:
        print(f"   ✅ Đã tạo {i + 1} sản phẩm...")

print(f"✅ Tạo thành công {products_created} sản phẩm!")

# Danh sách họ tên Việt Nam
ho = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 
      'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý']
ten_dem = ['Văn', 'Thị', 'Hữu', 'Đức', 'Minh', 'Anh', 'Quốc', 'Thanh', 'Tuấn', 'Hoài']
ten = ['Anh', 'Bình', 'Cường', 'Dũng', 'Hùng', 'Khoa', 'Long', 'Minh', 'Nam', 'Phong',
       'Quân', 'Sơn', 'Tài', 'Tùng', 'Vinh', 'Hà', 'Hương', 'Lan', 'Linh', 'Mai',
       'Ngọc', 'Phương', 'Thảo', 'Thu', 'Trang', 'Vy', 'Yến']

dia_chi = ['Hà Nội', 'TP.HCM', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Biên Hòa', 'Nha Trang',
           'Huế', 'Buôn Ma Thuột', 'Quy Nhơn', 'Vũng Tàu', 'Nam Định', 'Thái Nguyên']

# Tạo 500 khách hàng
print("\n🔄 Đang tạo 500 khách hàng...")
customers_created = 0

for i in range(500):
    ho_name = random.choice(ho)
    ten_dem_name = random.choice(ten_dem) if random.random() > 0.3 else ''
    ten_name = random.choice(ten)
    
    tenkhachhang = f"{ho_name} {ten_dem_name} {ten_name}".replace('  ', ' ').strip()
    tenkhachhangkhongdau = unidecode(tenkhachhang).lower()
    
    # Kiểm tra trùng
    if KhachHang.objects.filter(tenkhachhangkhongdau=tenkhachhangkhongdau).exists():
        continue
    
    diachi = f"{random.randint(1, 500)} {random.choice(['Lê Lợi', 'Trần Phú', 'Nguyễn Huệ', 'Hai Bà Trưng', 'Điện Biên Phủ'])}, {random.choice(dia_chi)}"
    
    KhachHang.objects.create(
        tenkhachhang=tenkhachhang,
        tenkhachhangkhongdau=tenkhachhangkhongdau,
        diachi=diachi,
        user=user
    )
    customers_created += 1
    
    if (i + 1) % 100 == 0:
        print(f"   ✅ Đã tạo {i + 1} khách hàng...")

print(f"✅ Tạo thành công {customers_created} khách hàng!")