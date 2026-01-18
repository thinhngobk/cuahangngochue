# views/receipt_views.py
"""
API liên quan đến Phiếu thu
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from app_quan_ly.models import KhachHang, PhieuThu, HoaDonBan,SoCaiCongNo
from .helper_views import update_ledger
from django.views.decorators.http import require_POST
from ..decorators import manager_or_higher, staff_or_higher
def save_receipt(request):
    """API tạo phiếu thu (từ frontend)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            khach_id = data.get('khach_id')
            if not khach_id:
                return JsonResponse({'status': 'error', 'message': 'Chưa chọn khách hàng'}, status=400)
            
            khach = KhachHang.objects.get(id=khach_id)
            
            phieu = PhieuThu.objects.create(
                khachhang=khach,
                mahoadon=data.get('ma_hd', ''),
                sotienthu=data.get('so_tien', 0),
                hinhthucthanhtoan=data.get('phuong_thuc', 'Tiền mặt'),
                user=request.user,
                ghichu=data.get('ghi_chu', '')
            )
            
            return JsonResponse({
                'status': 'success', 
                'maphieuthu': phieu.maphieuthu
            })
            
        except KhachHang.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Khách hàng không tồn tại'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def danh_sach_phieu_thu(request):
    """Trang danh sách phiếu thu"""
    queryset = PhieuThu.objects.all().order_by('-ngaylap')

    # Lọc dữ liệu
    search_query = request.GET.get('search', '')
    tu_ngay = request.GET.get('tu_ngay')
    den_ngay = request.GET.get('den_ngay')
    nguoi_lap_id = request.GET.get('nguoi_lap')

    if search_query:
        queryset = queryset.filter(
            Q(khachhang__tenkhachhang__icontains=search_query) | 
            Q(maphieuthu__icontains=search_query)
        )
    if tu_ngay:
        queryset = queryset.filter(ngaylap__date__gte=tu_ngay)
    if den_ngay:
        queryset = queryset.filter(ngaylap__date__lte=den_ngay)
    if nguoi_lap_id:
        queryset = queryset.filter(nguoi_lap_id=nguoi_lap_id)

    tong_thu = sum(p.sotienthu for p in queryset)

    # Phân trang
    paginator = Paginator(queryset, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    khach_hang_list = KhachHang.objects.all().order_by('tenkhachhang')
    danh_sach_nv = User.objects.all()

    return render(request, 'danh_sach_phieu_thu.html', {
        'phieu_thu_list': page_obj,
        'tong_thu': tong_thu,
        'khach_hang_list': khach_hang_list,
        'danh_sach_nv': danh_sach_nv,
        'search_query': search_query,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'nguoi_lap_id': nguoi_lap_id
    })

@require_POST
@staff_or_higher  # ← THÊM
@transaction.atomic
def luu_phieu_thu_nhanh(request):
    """Lưu hoặc cập nhật phiếu thu"""
    try:
        phieu_id = request.POST.get('phieu_id')
        
        # Nếu đang sửa
        if phieu_id:
            phieu_thu = get_object_or_404(PhieuThu, id=phieu_id)
            
            # Chặn sửa phiếu đính kèm hóa đơn
            if phieu_thu.mahoadon:
                return JsonResponse({
                    'status': 'error',
                    'message': f'❌ Không thể sửa phiếu thu đính kèm hóa đơn {phieu_thu.mahoadon}'
                }, status=400)
            
            # Cập nhật thông tin
            phieu_thu.khachhang_id = request.POST.get('khachhang_id')
            phieu_thu.sotienthu = request.POST.get('so_tien')
            phieu_thu.hinhthucthanhtoan = request.POST.get('hinh_thuc', 'Tiền mặt')
            phieu_thu.ghichu = request.POST.get('ghi_chu', '')
            phieu_thu.save()
            
            return JsonResponse({
                'status': 'success',
                'message': '✅ Đã cập nhật phiếu thu',
                'phieu_id': phieu_thu.id
            })
        else:
            # Tạo mới
            kh_id = request.POST.get('khachhang_id')
            so_tien = request.POST.get('so_tien')
            hinh_thuc = request.POST.get('hinh_thuc', 'Tiền mặt')
            ghi_chu = request.POST.get('ghi_chu', '')
            
            # Validate
            if not kh_id or not so_tien:
                return JsonResponse({
                    'status': 'error',
                    'message': '❌ Thiếu thông tin khách hàng hoặc số tiền'
                }, status=400)
            
            trang_thai = 'approved' if request.user.is_superuser else 'pending'
            
            phieu_thu = PhieuThu.objects.create(
                khachhang_id=kh_id,
                sotienthu=so_tien,
                hinhthucthanhtoan=hinh_thuc,
                ghichu=ghi_chu,
                trang_thai_duyet=trang_thai,
                user=request.user,
            )
            
            return JsonResponse({
                'status': 'success',
                'message': '✅ Đã tạo phiếu thu mới',
                'phieu_id': phieu_thu.id
            })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'❌ Lỗi: {str(e)}'
        }, status=500)
@require_POST
@staff_or_higher  # ← SỬA: Staff có thể hủy pending, Manager hủy tất cả
@transaction.atomic
def huy_phieu_thu(request, pk):
    """Hủy phiếu thu"""
    try:
        phieu = PhieuThu.objects.get(pk=pk)
        
        if phieu.trang_thai_duyet == 'canceled':
            return JsonResponse({
                'status': 'error',
                'message': 'Phiếu đã bị hủy rồi!'
            })
        
        # Chỉ Manager/Admin mới hủy được phiếu đã duyệt
        if phieu.trang_thai_duyet == 'approved':
            user_groups = list(request.user.groups.values_list('name', flat=True))
            is_manager_or_admin = request.user.is_superuser or 'Manager' in user_groups or 'Admin' in user_groups
            
            if not is_manager_or_admin:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Chỉ Manager/Admin mới hủy được phiếu đã duyệt!'
                }, status=403)
            
            # Ghi sổ đảo ngược
            khach = phieu.khachhang
            last_entry = SoCaiCongNo.objects.filter(
                khachhang=khach
            ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
            
            no_hien_tai = Decimal(str(last_entry.du_no_tuc_thoi)) if last_entry else Decimal(str(khach.no_dau_ky))
            tang = Decimal(str(phieu.sotienthu))
            no_moi = no_hien_tai + tang
            
            SoCaiCongNo.objects.create(
                khachhang=khach,
                ma_chung_tu=f"HUY-{phieu.maphieuthu}",
                dien_giai=f"Hủy phiếu thu {phieu.maphieuthu}",
                tang=tang,
                giam=0,
                du_no_tuc_thoi=no_moi,
                user=request.user,
                ghichu="Hệ thống tự động điều chỉnh khi hủy phiếu"
            )
        
        # Hủy phiếu (Staff hủy pending, Manager hủy tất cả)
        phieu.trang_thai_duyet = 'canceled'
        phieu.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã hủy phiếu thu thành công!'
        })
        
    except PhieuThu.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy phiếu thu!'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Lỗi: {str(e)}'
        }, status=500)
@require_POST
@manager_or_higher
@transaction.atomic
def duyet_phieu_thu(request, pk):
    """Duyệt phiếu thu"""
    try:
        phieu = PhieuThu.objects.get(pk=pk)
        
        if phieu.trang_thai_duyet == 'approved':
            return JsonResponse({
                'status': 'error',
                'message': 'Phiếu thu đã được duyệt rồi!'
            })
        
        if phieu.trang_thai_duyet == 'canceled':
            return JsonResponse({
                'status': 'error',
                'message': 'Không thể duyệt phiếu đã hủy!'
            })
        
        # Duyệt phiếu → Signal tự động ghi sổ
        phieu.trang_thai_duyet = 'approved'
        phieu.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Đã duyệt phiếu thu thành công!'
        })
        
    except PhieuThu.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy phiếu thu!'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Lỗi: {str(e)}'
        }, status=500)