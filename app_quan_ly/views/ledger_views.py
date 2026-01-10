# views/ledger_views.py
"""
API liên quan đến Sổ cái công nợ
"""
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum
from app_quan_ly.models import (
    KhachHang, HoaDonBan, PhieuThu, HoaDonHoan, SoCaiCongNo
)
from django.db import transaction
from django.utils import timezone  # ✅ THÊM DÒNG NÀY
from decimal import Decimal

def get_customer_ledger_api(request, kh_id):
    """Lấy chi tiết lịch sử nợ (Sổ chi tiết công nợ)"""
    kh = get_object_or_404(KhachHang, id=kh_id)
    
    # Lấy tất cả các giao dịch liên quan
    hds = HoaDonBan.objects.filter(khachhang=kh, trangthaidon='approved')
    pts = PhieuThu.objects.filter(khachhang=kh)
    hhs = HoaDonHoan.objects.filter(khachhang=kh, trangthaiduyet='approved')
    
    # Gộp lại và sắp xếp theo thời gian
    ledger = []
    
    # Thêm nợ đầu kỳ
    ledger.append({
        'ngay': '---',
        'noi_dung': 'Nợ đầu kỳ',
        'tang': float(kh.no_dau_ky),
        'giam': 0,
    })

    for x in hds:
        ledger.append({
            'ngay': x.ngaytao, 
            'noi_dung': f'Hóa đơn {x.mahoadonban}', 
            'tang': float(x.tongtienphaithanhtoan), 
            'giam': 0
        })
    for x in pts:
        ledger.append({
            'ngay': x.ngaylap, 
            'noi_dung': f'Phiếu thu {x.maphieuthu}', 
            'tang': 0, 
            'giam': float(x.sotienthu)
        })
    for x in hhs:
        ledger.append({
            'ngay': x.ngaylap, 
            'noi_dung': f'Hoàn hàng {x.mahoadonhoan}', 
            'tang': 0, 
            'giam': float(x.tongtienhoan)
        })
    
    return JsonResponse({
        'ten_khach': kh.tenkhachhang,
        'du_no_cuoi': float(kh.du_no_hien_tai),
        'history': ledger
    })


def api_so_chi_tiet_no(request, kh_id):
    """API lấy sổ chi tiết công nợ từ bảng SoCaiCongNo"""
    kh = get_object_or_404(KhachHang, id=kh_id)
    logs = SoCaiCongNo.objects.filter(khachhang=kh).order_by('ngay_ghi_so')
    
    data = []
    # Dòng đầu kỳ
    data.append({
        'ngay': '---',
        'chung_tu': 'Đầu kỳ',
        'dien_giai': 'Số dư nợ đầu kỳ',
        'tang': 0,
        'giam': 0,
        'du_no': int(kh.no_dau_ky),
        'ghi_chu': kh.ghichu 
    })
    
    for log in logs:
        data.append({
            'ngay': log.ngay_ghi_so.strftime("%d/%m/%Y %H:%M"),
            'chung_tu': log.ma_chung_tu,
            'dien_giai': log.dien_giai,
            'tang': int(log.tang),
            'giam': int(log.giam),
            'du_no': int(log.du_no_tuc_thoi),
            'ghi_chu': log.ghichu
        })
    
    return JsonResponse({'status': 'success', 'ledger': data})


def xem_so_cai(request):
    """Trang xem sổ cái công nợ"""
    kh_id = request.GET.get('khach_hang_id')
    tu_ngay = request.GET.get('tu_ngay')
    den_ngay = request.GET.get('den_ngay')
    
    so_cai_list = []
    du_no_dau_ky = 0
    du_no_cuoi_ky = 0
    tong_tang = 0
    tong_giam = 0
    
    # ✅ THÊM: Biến đối chiếu
    audit_result = None

    if kh_id:
        kh = get_object_or_404(KhachHang, id=kh_id)
        qs = SoCaiCongNo.objects.filter(khachhang=kh).select_related('user')

        # Tính dư nợ đầu kỳ
        if tu_ngay:
            ban_ghi_truoc = qs.filter(ngay_ghi_so__lt=tu_ngay).order_by('ngay_ghi_so', 'id').last()
            if ban_ghi_truoc:
                du_no_dau_ky = ban_ghi_truoc.du_no_tuc_thoi

        # Lọc danh sách trong kỳ
        if tu_ngay:
            qs = qs.filter(ngay_ghi_so__gte=tu_ngay)
        if den_ngay:
            qs = qs.filter(ngay_ghi_so__lte=den_ngay)

        so_cai_list = qs.order_by('ngay_ghi_so', 'id')

        # Tính tổng phát sinh & dư cuối
        stats = qs.aggregate(t=Sum('tang'), g=Sum('giam'))
        tong_tang = stats['t'] or 0
        tong_giam = stats['g'] or 0
        
        last_rec = so_cai_list.last()
        du_no_cuoi_ky = last_rec.du_no_tuc_thoi if last_rec else du_no_dau_ky
        
        # ✅ THÊM: Đối chiếu tự động
        audit_result = doi_chieu_cong_no_khach_hang(kh_id)

    return render(request, 'so_cai_cong_no.html', {
        'danh_sach_khach_hang': KhachHang.objects.all(),
        'so_cai_list': so_cai_list,
        'kh_id_selected': kh_id,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'du_no_dau_ky': du_no_dau_ky,
        'du_no_cuoi_ky': du_no_cuoi_ky,
        'tong_tang': tong_tang,
        'tong_giam': tong_giam,
        # ✅ THÊM: Kết quả audit
        'audit': audit_result,
    })


# ✅ THÊM: Hàm đối chiếu
def doi_chieu_cong_no_khach_hang(kh_id):
    """Đối chiếu công nợ giữa sổ cái và chứng từ gốc"""
    from django.db.models import Sum
    
    kh = KhachHang.objects.get(id=kh_id)
    
    # 1. Dư nợ theo SỔ CÁI
    so_du_so_cai = SoCaiCongNo.objects.filter(
        khachhang=kh
    ).order_by('-ngay_ghi_so', '-id').first()
    
    du_no_so_cai = so_du_so_cai.du_no_tuc_thoi if so_du_so_cai else kh.no_dau_ky
    
    # 2. Dư nợ theo CHỨNG TỪ
    tong_hd = HoaDonBan.objects.filter(
        khachhang=kh,
        trangthaidon='approved'
    ).aggregate(Sum('tongtienphaithanhtoan'))['tongtienphaithanhtoan__sum'] or 0
    
    tong_pt = PhieuThu.objects.filter(
        khachhang=kh,
        trang_thai_duyet='approved'
    ).aggregate(Sum('sotienthu'))['sotienthu__sum'] or 0
    
    tong_hh = HoaDonHoan.objects.filter(
        khachhang=kh,
        trangthaiduyet='approved'
    ).aggregate(Sum('tongtienhoan'))['tongtienhoan__sum'] or 0
    
    du_no_chung_tu = kh.no_dau_ky + tong_hd - tong_pt - tong_hh
    
    # 3. So sánh
    chenh_lech = du_no_so_cai - du_no_chung_tu
    khop = abs(chenh_lech) < 1  # Cho phép sai số 1đ
    
    return {
        'no_dau_ky': kh.no_dau_ky,
        'du_no_so_cai': du_no_so_cai,
        'tong_hd': tong_hd,
        'tong_pt': tong_pt,
        'tong_hh': tong_hh,
        'du_no_chung_tu': du_no_chung_tu,
        'chenh_lech': chenh_lech,
        'khop': khop,
    }

def update_ghi_chu_so_cai(request):
    """API cập nhật ghi chú sổ cái"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('id')
            ghi_chu = data.get('ghi_chu', '')
            
            # ✅ Validate
            if not item_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu ID'}, status=400)
            
            item = SoCaiCongNo.objects.get(id=item_id)
            item.ghichu = ghi_chu
            item.save(update_fields=['ghichu'])  # ✅ Chỉ update field này, tránh conflict
            
            return JsonResponse({
                'status': 'success',
                'message': 'Đã lưu ghi chú'
            })
            
        except SoCaiCongNo.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Không tìm thấy dữ liệu'
            }, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Dữ liệu JSON không hợp lệ'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Lỗi: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Chỉ chấp nhận POST request'
    }, status=405)
def update_ledger(khachhang, ma_ct, dien_giai, tang, giam, ghi_chu, user):
    """Helper function để ghi sổ cái công nợ"""
    with transaction.atomic():
        # Kiểm tra trùng
        if SoCaiCongNo.objects.filter(ma_chung_tu=ma_ct).exists():
            return
        
        # Lấy dư nợ hiện tại với lock
        last_entry = SoCaiCongNo.objects.filter(
            khachhang=khachhang
        ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
        
        if last_entry:
            no_hien_tai = Decimal(str(last_entry.du_no_tuc_thoi))
        else:
            no_hien_tai = Decimal(str(khachhang.no_dau_ky))
        
        # Tính dư nợ mới
        tang_decimal = Decimal(str(tang))
        giam_decimal = Decimal(str(giam))
        no_moi = no_hien_tai + tang_decimal - giam_decimal
        
        # Ghi sổ
        SoCaiCongNo.objects.create(
            khachhang=khachhang,
            ma_chung_tu=ma_ct,
            dien_giai=dien_giai,
            tang=tang_decimal,
            giam=giam_decimal,
            du_no_tuc_thoi=no_moi,
            user=user,
            ghichu=ghi_chu
        )
