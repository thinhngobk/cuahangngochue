from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app_quan_ly.models import SanPham, KhachHang, HoaDonBan, ChiTietHoaDonBan
from decimal import Decimal
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Generate fake data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--products', type=int, default=4000, help='Number of products')
        parser.add_argument('--customers', type=int, default=500, help='Number of customers')
        parser.add_argument('--invoices', type=int, default=10000, help='Number of invoices')

    def handle(self, *args, **options):
        num_products = options['products']
        num_customers = options['customers']
        num_invoices = options['invoices']

        self.stdout.write('🚀 Bắt đầu tạo fake data...\n')

        # Lấy user mặc định
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('❌ Không tìm thấy user! Tạo user trước.'))
                return

        # ===== 1. TẠO SẢN PHẨM =====
        self.stdout.write('📦 Đang tạo sản phẩm...')
        
        categories = ['Điện thoại', 'Laptop', 'Tai nghe', 'Chuột', 'Bàn phím', 
                      'Màn hình', 'Ốp lưng', 'Sạc', 'Cáp', 'Pin']
        
        products_batch = []
        for i in range(num_products):
            category = random.choice(categories)
            ten = f"{category} Model {i+1:05d}"
            
            products_batch.append(SanPham(
                tensanpham=ten,
                tensanphamkhongdau=self.remove_accents(ten).lower(),
                donvitinh=random.choice(['Cái', 'Chiếc', 'Bộ', 'Hộp']),
                dongiagoc=Decimal(random.randint(50000, 500000)),
                dongiaban=Decimal(random.randint(100000, 1000000)),
                tonkho=random.randint(0, 1000),
                ghichu=f'Sản phẩm test {i+1}',
                user=user
            ))
            
            # Bulk create mỗi 500 records
            if len(products_batch) >= 500:
                SanPham.objects.bulk_create(products_batch, ignore_conflicts=True)
                self.stdout.write(f'  ✓ Đã tạo {i+1}/{num_products} sản phẩm')
                products_batch = []
        
        # Tạo phần còn lại
        if products_batch:
            SanPham.objects.bulk_create(products_batch, ignore_conflicts=True)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo {SanPham.objects.count()} sản phẩm\n'))

        # ===== 2. TẠO KHÁCH HÀNG =====
        self.stdout.write('👥 Đang tạo khách hàng...')
        
        ho_list = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng']
        ten_list = ['Văn', 'Thị', 'Minh', 'Anh', 'Hồng', 'Lan', 'Hùng', 'Dũng', 'Linh', 'Hương']
        ten_dem = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'K', 'L', 'M', 'N', 'P', 'Q', 'R']
        
        customers_batch = []
        for i in range(num_customers):
            ho = random.choice(ho_list)
            dem = random.choice(ten_dem)
            ten = random.choice(ten_list)
            ten_day = f"{ho} {dem} {ten}"
            
            customers_batch.append(KhachHang(
                tenkhachhang=ten_day,
                tenkhachhangkhongdau=self.remove_accents(ten_day).lower(),
                sdt=f"09{random.randint(10000000, 99999999)}",
                diachi=f"Số {random.randint(1, 999)}, Quận {random.randint(1, 12)}, TP.HCM",
                no_dau_ky=Decimal(random.randint(0, 5000000)),
                ghichu=f'Khách hàng test {i+1}',
                user=user
            ))
            
            # Bulk create mỗi 100 records
            if len(customers_batch) >= 100:
                KhachHang.objects.bulk_create(customers_batch, ignore_conflicts=True)
                self.stdout.write(f'  ✓ Đã tạo {i+1}/{num_customers} khách hàng')
                customers_batch = []
        
        # Tạo phần còn lại
        if customers_batch:
            KhachHang.objects.bulk_create(customers_batch, ignore_conflicts=True)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo {KhachHang.objects.count()} khách hàng\n'))

        # ===== 3. TẠO HÓA ĐƠN =====
        self.stdout.write('📄 Đang tạo hóa đơn...')
        
        all_products = list(SanPham.objects.all()[:2000])  # Lấy 2000 SP để random
        all_customers = list(KhachHang.objects.all())
        
        if not all_products:
            self.stdout.write(self.style.ERROR('❌ Không có sản phẩm để tạo hóa đơn!'))
            return
        
        if not all_customers:
            self.stdout.write(self.style.ERROR('❌ Không có khách hàng để tạo hóa đơn!'))
            return
        
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(num_invoices):
            ngay_lap = start_date + timedelta(days=random.randint(0, 365))
            khach = random.choice(all_customers)
            
            # Random sản phẩm trước
            num_items = random.randint(2, 7)
            selected_products = random.sample(all_products, min(num_items, len(all_products)))
            
            # TÍNH TOÁN TỔNG TIỀN TRƯỚC
            tong_tien = Decimal('0')
            chi_tiet_data = []
            
            for sp in selected_products:
                sl = random.randint(1, 10)
                gia = sp.dongiaban
                thanh_tien = Decimal(sl) * gia
                tong_tien += thanh_tien
                
                chi_tiet_data.append({
                    'sp': sp,
                    'sl': sl,
                    'gia': gia,
                    'thanh_tien': thanh_tien
                })
            
            # Tính chiết khấu và tổng cuối
            ck_tong = Decimal(random.choice([0, 5, 10, 15]))
            tong_sau_ck = tong_tien * (1 - ck_tong / 100)
            ung_tien = Decimal(random.randint(0, int(tong_sau_ck)))
            
            # ← THÊM: Retry khi trùng mã
            max_retries = 5
            hd = None
            
            for retry in range(max_retries):
                try:
                    # TẠO HÓA ĐƠN
                    hd = HoaDonBan.objects.create(
                        khachhang=khach,
                        ngaylap=ngay_lap.date(),
                        chietkhauchung=ck_tong,
                        tongtienphaithanhtoan=int(tong_sau_ck),
                        khachhangungtien=ung_tien,
                        trangthaidon=random.choice(['pending', 'approved', 'approved', 'approved']),
                        ghichu=f'Hóa đơn test {i+1}',
                        user=user
                    )
                    break  # Thành công → Thoát loop
                except Exception as e:
                    if 'duplicate key' in str(e) and retry < max_retries - 1:
                        # Trùng mã → Thử lại
                        continue
                    else:
                        # Lỗi khác hoặc hết retry → Raise
                        raise
            
            if not hd:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Bỏ qua hóa đơn {i+1} (không tạo được mã unique)'))
                continue
            
            # Tạo chi tiết
            chi_tiet_batch = []
            for item in chi_tiet_data:
                chi_tiet_batch.append(ChiTietHoaDonBan(
                    hoadonban=hd,
                    sanpham=item['sp'],
                    tensanpham=item['sp'].tensanpham,
                    donvitinh=item['sp'].donvitinh,
                    soluong=item['sl'],
                    dongiagoc=item['sp'].dongiagoc,
                    dongiaban=item['gia'],
                    chietkhau=Decimal('0'),
                    thanhtien=item['thanh_tien'],
                    user=user
                ))
            
            ChiTietHoaDonBan.objects.bulk_create(chi_tiet_batch)
            
            if (i + 1) % 100 == 0:
                self.stdout.write(f'  ✓ Đã tạo {i+1}/{num_invoices} hóa đơn')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo {HoaDonBan.objects.count()} hóa đơn\n'))
        
        # THỐNG KÊ
        self.stdout.write(self.style.SUCCESS('\n🎉 HOÀN THÀNH!'))
        self.stdout.write(f'\n📊 Thống kê:')
        self.stdout.write(f'  - Sản phẩm: {SanPham.objects.count()}')
        self.stdout.write(f'  - Khách hàng: {KhachHang.objects.count()}')
        self.stdout.write(f'  - Hóa đơn: {HoaDonBan.objects.count()}')
        self.stdout.write(f'  - Chi tiết HĐ: {ChiTietHoaDonBan.objects.count()}')

    def remove_accents(self, text):
        """Loại bỏ dấu tiếng Việt"""
        replacements = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'đ': 'd',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        }
        result = text.lower()
        for viet, latin in replacements.items():
            result = result.replace(viet, latin)
        return result