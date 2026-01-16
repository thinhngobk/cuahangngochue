import time
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app_quan_ly.models import KhachHang, SoCaiCongNo
import json
from django.db import models
@login_required
def index_view(request):
    """Trang chủ Dashboard"""
    return render(request, 'index.html')


@login_required
def pos_view(request):
    start = time.time() 
    # Query customers với prefetch
    t1 = time.time()
    khach_hang_list = KhachHang.objects.prefetch_related(
        models.Prefetch(
            'so_no_rieng',  # ← Dùng related_name
            queryset=SoCaiCongNo.objects.order_by('-ngay_ghi_so', '-id')[:1],
            to_attr='so_no_latest'
        )
    ).order_by('-id')
    count = khach_hang_list.count()
    
    # Build customers list
    t2 = time.time()
    customers = []
    for kh in khach_hang_list:
        # Lấy dư nợ từ prefetch
        if hasattr(kh, 'so_no_latest') and kh.so_no_latest:
            du_no = float(kh.so_no_latest[0].du_no_tuc_thoi)
        else:
            du_no = float(kh.no_dau_ky)
        
        customers.append({
            'id': kh.id,
            'ten': kh.tenkhachhang,
            'sdt': kh.sdt or '',
            'tong_no': du_no
        })
    
    # Session cleanup
    t3 = time.time()
    if 'edit_invoice_data' in request.session:
        del request.session['edit_invoice_data']
    
    # JSON serialize
    t4 = time.time()
    customers_json = json.dumps(customers)
    
    context = {
        'customers_json': customers_json
    }
    
    # Render template
    t5 = time.time()
    response = render(request, 'pos.html', context)
    total = (time.time() - start) * 1000
    
    return response
@login_required
def pos_hoan_view(request):
    khach_hangs = KhachHang.objects.prefetch_related(
        models.Prefetch(
            'so_no_rieng',
            queryset=SoCaiCongNo.objects.order_by('-ngay_ghi_so', '-id')[:1],
            to_attr='so_no_latest'
        )
    ).order_by('-id')
    
    customers = []
    for kh in khach_hangs:
        if hasattr(kh, 'so_no_latest') and kh.so_no_latest:
            du_no = float(kh.so_no_latest[0].du_no_tuc_thoi)
        else:
            du_no = float(kh.no_dau_ky)
        
        customers.append({
            'id': kh.id,
            'ten': kh.tenkhachhang,
            'sdt': kh.sdt or '',
            'tong_no': du_no
        })
    
    return render(request, 'pos_hoan.html', {
        'customers_json': json.dumps(customers)
    })

def invoice_hoan_manager_view(request):
    """Trang lịch sử đơn hoàn"""
    return render(request, 'invoice_hoan_manager.html')


def invoice_manager_view(request):
    """Trang quản lý danh sách hóa đơn"""
    return render(request, 'invoice_manager.html')
@login_required
def get_products_api(request):
    products = SanPham.objects.only(
        'id', 'masanpham', 'barcode', 'tensanpham', 
        'donvitinh', 'dongiagoc', 'dongiaban', 'tonkho', 
        'is_active', 'ghichu'
    ).all()
    
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
    customers = KhachHang.objects.prefetch_related(
        models.Prefetch(
            'so_no_rieng',
            queryset=SoCaiCongNo.objects.order_by('-ngay_ghi_so', '-id')[:1],
            to_attr='so_no_latest'
        )
    )
    
    data = []
    for kh in customers:
        if hasattr(kh, 'so_no_latest') and kh.so_no_latest:
            du_no = float(kh.so_no_latest[0].du_no_tuc_thoi)
        else:
            du_no = float(kh.no_dau_ky)
        
        data.append({
            'id': kh.id,
            'ma': kh.makhachhang,
            'ten': kh.tenkhachhang,
            'sdt': kh.sdt,
            'email': kh.email,
            'diachi': kh.diachi,
            'phan_loai': kh.phanloai,
            'du_no': du_no,
            'han_muc_no': float(kh.han_muc_no),
            'mst': kh.mst,
            'ghichu': kh.ghichu
        })
    
    return JsonResponse(data, safe=False)
def customer_manager(request):
    """Trang quản lý khách hàng"""
    customers = KhachHang.objects.filter(is_active=True).order_by('-id')
    customers_data = [{
        'id': kh.id,
        'ma': kh.makhachhang,
        'ten': kh.tenkhachhang,
        'sdt': kh.sdt or '',
        'email': kh.email or '',
        'diachi': kh.diachi or '',
        'phan_loai': kh.phanloai,
        'du_no': float(kh.du_no_hien_tai),
        'no_dau_ky': float(kh.no_dau_ky),
        'han_muc_no': float(kh.han_muc_no),
        'is_active': kh.is_active,
        'mst': kh.mst or '',
        'ghichu': kh.ghichu or ''
    } for kh in customers]
    
    context = {
        'customers_json': json.dumps(customers_data, ensure_ascii=False)
    }
    return render(request, 'customer_manager.html', context)
def product_manager(request):
    """Trang quản lý sản phẩm"""
    return render(request, 'product_manager.html')