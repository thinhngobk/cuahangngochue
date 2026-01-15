# views/customer_views.py
"""
API liên quan đến Khách hàng
"""
import json
from decimal import Decimal
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from unidecode import unidecode
from app_quan_ly.models import KhachHang
from django.shortcuts import render
@transaction.atomic
def edit_customer(request, kh_id):
    """Sửa thông tin khách hàng"""
    kh = KhachHang.objects.get(id=kh_id)
    data = json.loads(request.body)
    
    # ✅ CHỈ CHO SỬA CÁC TRƯỜNG NÀY
    kh.tenkhachhang = data.get('ten', kh.tenkhachhang)
    kh.sdt = data.get('sdt', kh.sdt)
    kh.diachi = data.get('diachi', kh.diachi)
    kh.email = data.get('email', kh.email)
    kh.mst = data.get('mst', kh.mst)
    kh.phanloai = data.get('phanloai', kh.phanloai)
    kh.han_muc_no = data.get('han_muc_no', kh.han_muc_no)
    kh.ghichu = data.get('ghichu', kh.ghichu)
    
    # ❌ KHÔNG CHO SỬA no_dau_ky
    
    kh.save()
    return JsonResponse({'status': 'success'})
@transaction.atomic
def add_customer_fast(request):
    """API thêm nhanh khách hàng với đầy đủ thông tin"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate dữ liệu bắt buộc
            ten_kh = data.get('ten', '').strip()
            if not ten_kh:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Tên khách hàng không được để trống'
                }, status=400)
            
            # Lấy và xử lý dữ liệu
            sdt = data.get('sdt', '').strip()
            phanloai = data.get('phanloai', 'LE')
            diachi = data.get('diachi', '').strip()
            email = data.get('email', '').strip()
            mst = data.get('mst', '').strip()
            ghichu = data.get('ghichu', '').strip()
            
            # Xử lý số nợ và hạn mức
            try:
                no_dau_ky = Decimal(str(data.get('no_dau_ky', 0)))
            except (ValueError, Exception):
                no_dau_ky = Decimal('0')
            
            try:
                han_muc_no = Decimal(str(data.get('han_muc_no', 0)))
            except (ValueError, Exception):
                han_muc_no = Decimal('0')
            
            # Validate phân loại
            if phanloai not in ['LE', 'SI']:
                phanloai = 'LE'
            
            # Tạo khách hàng mới
            kh = KhachHang.objects.create(
                tenkhachhang=ten_kh,
                sdt=sdt,
                phanloai=phanloai,
                diachi=diachi,
                email=email,
                mst=mst,
                no_dau_ky=no_dau_ky,
                han_muc_no=han_muc_no,
                ghichu=ghichu,
                user=request.user,
                is_active=True
            )
            
            return JsonResponse({
                'status': 'success', 
                'id': kh.id, 
                'ten': kh.tenkhachhang,
                'sdt': kh.sdt,
                'phanloai': kh.get_phanloai_display(),
                'message': f'Đã thêm khách hàng: {kh.tenkhachhang}'
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Dữ liệu không hợp lệ: {str(e)}'
            }, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error', 
                'message': f'Lỗi hệ thống: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Phương thức không hợp lệ'
    }, status=405)
def customer_manager(request):
    """Trang quản lý khách hàng"""
    return render(request, 'customer_manager.html')
def get_customers_api(request):
    """API lấy danh sách khách hàng"""
    customers = KhachHang.objects.all().order_by('-id')
    data = [{
        'id': kh.id,
        'ma': kh.makhachhang,
        'ten': kh.tenkhachhang,
        'sdt': kh.sdt or '',
        'email': kh.email or '',
        'diachi': kh.diachi or '',
        'phan_loai': kh.phanloai,
        'du_no': float(kh.du_no_hien_tai),
        'no_dau_ky': float(kh.no_dau_ky),  # ← THÊM
        'han_muc_no': float(kh.han_muc_no),
        'mst': kh.mst or '',
        'ghichu': kh.ghichu or ''
    } for kh in customers]
    return JsonResponse(data, safe=False)
def get_customer_detail_api(request, kh_id):
    from django.shortcuts import get_object_or_404
    from app_quan_ly.models import KhachHang, SoCaiCongNo, PhieuThu

    # Kiểm tra ID và lấy khách hàng
    kh = get_object_or_404(KhachHang, id=kh_id)
    
    # Lấy sổ cái: Chú ý trường 'khachhang' (không gạch dưới) và 'tang'/'giam'
    # Dùng filter(khachhang=kh) vì lỗi trước đó báo 'khach_hang' không tồn tại
    ledger = SoCaiCongNo.objects.filter(khachhang=kh).order_by('-ngay_ghi_so', '-id')[:20]
    
    # Lấy phiếu thu
    receipts = PhieuThu.objects.filter(khachhang=kh).order_by('-ngaylap')[:10]
    
    return JsonResponse({
        'customer': {
            'ma': kh.makhachhang,
            'ten': kh.tenkhachhang,
            'du_no': float(kh.du_no_hien_tai),
            'no_dau_ky': float(kh.no_dau_ky),
            'phan_loai': kh.phanloai,
            'sdt': kh.sdt or '',
            'diachi': kh.diachi or '',
        },
        'entries': [{
            'ngay': e.ngay_ghi_so.strftime('%d/%m/%Y'),
            'ma': e.ma_chung_tu,
            'tang': float(e.tang),
            'giam': float(e.giam),
            'ton': float(e.du_no_tuc_thoi),
            'noidung': e.dien_giai
        } for e in ledger],
        'receipts': [{
            'ma': r.maphieuthu,
            'tien': float(r.sotienthu),
            'ngay': r.ngaylap.strftime('%d/%m/%Y')
        } for r in receipts]
    })
def search_customers_api(request):
    """
    API tìm kiếm khách hàng TỐI ƯU cho POS
    Autocomplete với debounce
    """
    q = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 15))
    
    # Nếu không search → Trả về danh sách gần đây
    if not q or len(q) < 2:
        customers = KhachHang.objects.filter(
            is_active=True
        ).order_by('-id')[:limit]
    else:
        q_khong_dau = unidecode(q).lower()
        
        # ✅ TÌM KIẾM CÓ THỨ TỰ ƯU TIÊN
        # 1. TÊN BẮT ĐẦU (ưu tiên cao nhất)
        # 2. TÊN CHỨA
        # 3. SĐT
        # 4. Mã KH (ít dùng nhất)
        
        from django.db.models import Case, When, Value, IntegerField
        
        customers = KhachHang.objects.filter(
            Q(tenkhachhangkhongdau__startswith=q_khong_dau) |  # Tên bắt đầu
            Q(tenkhachhangkhongdau__icontains=q_khong_dau) |   # Tên chứa
            Q(sdt__icontains=q) |                               # SĐT
            Q(makhachhang__iexact=q),                           # Mã KH
            is_active=True
        ).annotate(
            # Sắp xếp theo mức độ ưu tiên
            priority=Case(
                When(tenkhachhangkhongdau__startswith=q_khong_dau, then=Value(1)),
                When(tenkhachhangkhongdau__icontains=q_khong_dau, then=Value(2)),
                When(sdt__icontains=q, then=Value(3)),
                When(makhachhang__iexact=q, then=Value(4)),
                default=Value(5),
                output_field=IntegerField(),
            )
        ).order_by('priority', 'tenkhachhang').distinct()[:limit]
    
    # Serialize data
    data = [{
        'id': kh.id,
        'ma': kh.makhachhang,
        'ten': kh.tenkhachhang,
        'sdt': kh.sdt or '',
        'email': kh.email or '',
        'diachi': kh.diachi or '',
        'phan_loai': kh.phanloai,
        'phan_loai_text': kh.get_phanloai_display(),
        'du_no': float(kh.du_no_hien_tai),
        'han_muc_no': float(kh.han_muc_no),
        'trang_thai_no': kh.trang_thai_no,
    } for kh in customers]
    
    return JsonResponse(data, safe=False)
@transaction.atomic
def update_customer_api(request, kh_id):
    """API cập nhật thông tin khách hàng"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kh = KhachHang.objects.get(id=kh_id)
            
            # ✅ CHỈ CHO SỬA CÁC TRƯỜNG NÀY
            kh.tenkhachhang = data.get('ten', '').strip()
            kh.sdt = data.get('sdt', '').strip()
            kh.diachi = data.get('diachi', '').strip()
            kh.email = data.get('email', '').strip()
            kh.mst = data.get('mst', '').strip()
            kh.phanloai = data.get('phanloai', 'LE')
            kh.ghichu = data.get('ghichu', '').strip()
            
            # ❌ KHÔNG CHO SỬA: no_dau_ky, han_muc_no, du_no
            
            kh.save()
            return JsonResponse({'status': 'success', 'message': 'Cập nhật thành công'})
        except KhachHang.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Khách hàng không tồn tại'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
def get_customers_paginated_api(request):
    """
    API lấy danh sách khách hàng CÓ PHÂN TRANG
    Dùng cho trang Customer Manager
    """
    from django.core.paginator import Paginator
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    search = request.GET.get('search', '').strip()
    filter_type = request.GET.get('type', 'all')
    
    # Base queryset
    qs = KhachHang.objects.filter(is_active=True)
    
    # Search
    if search and len(search) >= 2:
        search_nd = unidecode(search).lower()
        qs = qs.filter(
            Q(tenkhachhangkhongdau__icontains=search_nd) |
            Q(sdt__icontains=search) |
            Q(makhachhang__iexact=search) |
            Q(email__icontains=search)
        )
    
    # Filter by type
    if filter_type != 'all':
        qs = qs.filter(phanloai=filter_type)
    
    # Paginate
    paginator = Paginator(qs.order_by('-id'), page_size)
    page_obj = paginator.get_page(page)
    
    data = {
        'customers': [{
            'id': kh.id,
            'ma': kh.makhachhang,
            'ten': kh.tenkhachhang,
            'sdt': kh.sdt or '',
            'email': kh.email or '',
            'diachi': kh.diachi or '',
            'phan_loai': kh.phanloai,
            'du_no': float(kh.du_no_hien_tai),
            'han_muc_no': float(kh.han_muc_no),
            'mst': kh.mst or '',
            'ghichu': kh.ghichu or '',
        } for kh in page_obj],
        'pagination': {
            'total': paginator.count,
            'page': page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_size': page_size,
        }
    }
    
    return JsonResponse(data)