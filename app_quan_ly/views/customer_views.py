# views/customer_views.py
"""
API liên quan đến Khách hàng
"""
import json
from decimal import Decimal
from django.http import JsonResponse
from django.db import transaction
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
        'han_muc_no': float(kh.han_muc_no),
        'mst': kh.mst or '',
        'ghichu': kh.ghichu or ''
    } for kh in customers]
    return JsonResponse(data, safe=False)