from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app_quan_ly.models import KhachHang, SoCaiCongNo
import json

@login_required
def index_view(request):
    """Trang chủ Dashboard"""
    return render(request, 'index.html')


@login_required
def pos_view(request):
    khach_hang_list = KhachHang.objects.all().order_by('-id')
    
    customers = []
    for kh in khach_hang_list:
        customers.append({
            'id': kh.id,
            'ten': kh.tenkhachhang,
            'sdt': kh.sdt or '',
            'tong_no': float(kh.du_no_hien_tai)
        })
    
    if 'edit_invoice_data' in request.session:
        del request.session['edit_invoice_data']
    
    context = {
        'customers_json': json.dumps(customers)
    }
    
    return render(request, 'pos.html', context)

@login_required
def pos_hoan_view(request):
    """Trang POS hoàn hàng"""
    khach_hangs = KhachHang.objects.all().order_by('-id')
    return render(request, 'pos_hoan.html', {'khach_hangs': khach_hangs})


def invoice_hoan_manager_view(request):
    """Trang lịch sử đơn hoàn"""
    return render(request, 'invoice_hoan_manager.html')


def invoice_manager_view(request):
    """Trang quản lý danh sách hóa đơn"""
    return render(request, 'invoice_manager.html')
@login_required
def get_products_api(request):
    products = SanPham.objects.all()
    data = [{
        'id': p.id,
        'ma': p.masanpham,
        'barcode': p.barcode,
        'ten': p.tensanpham,
        'donvi': p.donvitinh,
        'gia_goc': float(p.dongiagoc),
        'gia_ban': float(p.dongiaban),
        'ton_kho': p.tonkho,
        'is_active': p.is_active,
        'ghichu': p.ghichu
    } for p in products]
    return JsonResponse(data, safe=False)

# API Khách hàng
@login_required
def get_customers_api(request):
    customers = KhachHang.objects.all()
    data = [{
        'id': kh.id,
        'ma': kh.makhachhang,
        'ten': kh.tenkhachhang,
        'sdt': kh.sdt,
        'email': kh.email,
        'diachi': kh.diachi,
        'phan_loai': kh.phanloai,
        'du_no': float(kh.du_no_hien_tai),
        'han_muc_no': float(kh.han_muc_no),
        'mst': kh.mst,
        'ghichu': kh.ghichu
    } for kh in customers]
    return JsonResponse(data, safe=False)
def customer_manager(request):
    """Trang quản lý khách hàng"""
    return render(request, 'customer_manager.html')

def product_manager(request):
    """Trang quản lý sản phẩm"""
    return render(request, 'product_manager.html')