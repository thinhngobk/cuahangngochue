# views/return_views.py
"""
API liên quan đến Hóa đơn hoàn hàng
"""
import json
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from app_quan_ly.models import (
    HoaDonHoan, ChiTietHoaDonHoan, SanPham, SoCaiCongNo
)
from datetime import datetime, date

@transaction.atomic
def save_invoice_hoan(request):
    """API lưu đơn hoàn hàng"""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Hết phiên'}, status=401)
    
    try:
        # Lấy dữ liệu
        data = json.loads(request.body)
        items_data = data.get('items', [])
        if not items_data or len(items_data) == 0:
            return JsonResponse({'status': 'error', 'message': 'Giỏ hàng trống, không thể lưu!'}, status=400)
        is_admin = request.user.has_perm('app_name.approve_hoadonhoan')
        is_approve_request = data.get('admin_approve', False)

        should_approve_now = is_admin and is_approve_request
        trang_thai = 'approved' if should_approve_now else 'pending'

        # Tính tổng tiền hàng (để dùng cho final_total)
        tong_tien_hang = Decimal('0')
        for item in items_data:
            gia = Decimal(str(item.get('gia', 0)))
            sl = Decimal(str(item.get('soluong', 1)))
            ck_phan_tram = Decimal(str(item.get('ck_item', 0)))
            
            tien_truoc_ck = gia * sl
            tien_chiet_khau = tien_truoc_ck * (ck_phan_tram / 100)
            thanh_tien = tien_truoc_ck - tien_chiet_khau
            
            tong_tien_hang += thanh_tien

        # Áp dụng chiết khấu tổng đơn
        ck_tong = Decimal(str(data.get('chietkhau_tong') or 0))
        final_total = tong_tien_hang * (1 - ck_tong / 100)

        # 1. Tạo hóa đơn hoàn
        hh = HoaDonHoan.objects.create(
            khachhang_id=data.get('khachhang_id'),
            ngaylap=datetime.strptime(data.get('ngay_lap'), '%Y-%m-%d').date() if data.get('ngay_lap') else date.today(),
            tongtienhoan=int(final_total),
            trangthaiduyet=trang_thai,
            lydohoan=data.get('ghichu_don', ''),
            user=request.user
        )

        # 2. Lưu chi tiết
        for item in items_data:
            sp = SanPham.objects.get(id=int(item.get('id')))
            so_luong = Decimal(str(item.get('soluong') or 1))
            gia_ban = Decimal(str(item.get('gia') or 0))
            
            ck_phan_tram = Decimal(str(item.get('ck_item') or 0))
            tien_truoc_ck = so_luong * gia_ban
            tien_chiet_khau = tien_truoc_ck * (ck_phan_tram / 100)
            thanh_tien = tien_truoc_ck - tien_chiet_khau

            ChiTietHoaDonHoan.objects.create(
                hoadonhoan=hh, 
                sanpham=sp, 
                tensanpham=sp.tensanpham,
                donvitinh=item.get('donvi', sp.donvitinh), 
                soluong=so_luong, 
                dongiagoc=sp.dongiagoc, 
                dongialucban=gia_ban,
                chietkhau=tien_chiet_khau,
                thanhtien=thanh_tien,
                ghichu=item.get('ghichu_sp', ''),
                user=request.user
            )

        # 3. Nếu duyệt ngay → Cộng kho (signal sẽ lo ghi sổ)
        if should_approve_now:
            for ct in hh.chitiet_hoan.all():
                sp = ct.sanpham
                sp.tonkho += ct.soluong
                sp.save()

        return JsonResponse({
            'status': 'success', 
            'ma': hh.mahoadonhoan,
            'message': 'Đã lưu và duyệt đơn hoàn' if should_approve_now else 'Đã lưu đơn hoàn chờ duyệt'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_invoices_hoan_api(request):
    """API lấy danh sách đơn hoàn hàng"""
    try:
        ngay_loc = request.GET.get('date')
        ten_khach = request.GET.get('customer')
        tt_don = request.GET.get('status')
        page_number = request.GET.get('page', 1)
        page_size = 15

        hhs = HoaDonHoan.objects.select_related('khachhang').all().order_by('-ngaylap')

        if ngay_loc:
            hhs = hhs.filter(ngaylap__date=ngay_loc)
        if ten_khach:
            hhs = hhs.filter(khachhang__tenkhachhang__icontains=ten_khach)
        if tt_don and tt_don != 'all':
            hhs = hhs.filter(trangthaiduyet=tt_don)

        paginator = Paginator(hhs, page_size)
        page_obj = paginator.get_page(page_number)

        data_list = []
        for h in page_obj:
            data_list.append({
                'id': h.id,
                'ma_hd': h.mahoadonhoan,
                'ngay': h.ngaylap.strftime("%d/%m/%Y"),
                'khach': h.khachhang.tenkhachhang if h.khachhang else "Khách lẻ",
                'tong': float(h.tongtienhoan or 0),
                'trang_thai_don': h.get_trangthaiduyet_display(),
                'slug_status': h.trangthaiduyet,
            })
        
        return JsonResponse({
            'status': 'success', 
            'data': data_list,
            'meta': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_items': paginator.count
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_invoice_hoan_detail_api(request, ma_hd):
    """API lấy chi tiết đơn hoàn"""
    try:
        hh = HoaDonHoan.objects.filter(mahoadonhoan=ma_hd).first()
        if not hh:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy đơn hoàn'}, status=404)

        details = hh.chitiet_hoan.all()
        item_list = []
        
        for i in details:
            gia = float(i.dongialucban or 0)
            sl = float(i.soluong or 0)
            tien_ck = float(i.chietkhau or 0)
            
            tong_truoc_ck = gia * sl
            phan_tram_ck = (tien_ck / tong_truoc_ck * 100) if tong_truoc_ck > 0 else 0
            
            item_list.append({
                'id': i.sanpham.id,  # ✅ THÊM
                'ten': i.tensanpham,
                'sl': sl,
                'soluong': sl,  # ✅ THÊM - alias
                'dv': i.donvitinh or "-",
                'donvi': i.donvitinh or "-",  # ✅ THÊM - alias
                'gia': gia,
                'ck_tien': tien_ck,
                'ck_pt': round(phan_tram_ck, 1),
                'ck_item': round(phan_tram_ck, 1),  # ✅ THÊM - alias
                'thanh_tien': float(i.thanhtien or 0),
                'ghi_chu': i.ghichu or "",
                'ghichu_sp': i.ghichu or ""  # ✅ THÊM - alias
            })
        
        tong_cac_mon = sum(float(i.thanhtien or 0) for i in details)
        
        return JsonResponse({
            'status': 'success', 
            'data': {
                'id': hh.id,
                'ma_hd': hh.mahoadonhoan,
                'ngay': hh.ngaylap.strftime("%d/%m/%Y") if hh.ngaylap else "",
                'khach': hh.khachhang.tenkhachhang if hh.khachhang else "Khách lẻ",
                'khachhang_id': hh.khachhang.id if hh.khachhang else None,  # ✅ THÊM
                'tam_tinh': tong_cac_mon,
                'tong': float(hh.tongtienhoan or 0),
                'trang_thai_don': hh.get_trangthaiduyet_display(),
                'slug_trang_thai': hh.trangthaiduyet,
                'ghichu': hh.lydohoan or "",
                'items': item_list
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@transaction.atomic
def approve_invoice_hoan(request, hh_id):
    """
    API duyệt đơn hoàn hàng
    ✅ CHỈ XỬ LÝ KHO - Signal sẽ tự động ghi sổ công nợ
    """
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}, status=405)
    
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Chỉ admin mới có quyền duyệt'}, status=403)
    
    try:
        hh = HoaDonHoan.objects.select_for_update().get(id=hh_id)
        
        if hh.trangthaiduyet == 'approved':
            return JsonResponse({'status': 'error', 'message': 'Đơn hoàn này đã duyệt rồi'}, status=400)

        # 1. Cộng kho
        for ct in hh.chitiet_hoan.all():
            sp = ct.sanpham
            sp.tonkho += ct.soluong
            sp.save()

        # 2. Đổi trạng thái → Signal sẽ tự động ghi sổ
        hh.trangthaiduyet = 'approved'
        hh.ngayduyet = timezone.now()
        hh.save()
        
        # ✅ KHÔNG GỌI update_ledger() NỮA - Signal đã lo!
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Đã duyệt đơn hoàn {hh.mahoadonhoan} và cập nhật kho + sổ nợ'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@transaction.atomic
def cancel_invoice_hoan(request, hh_id):
    """
    API hủy đơn hoàn hàng
    ✅ XỬ LÝ THỦ CÔNG vì signal không cover trường hợp hủy
    """
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}, status=405)
    
    hh = get_object_or_404(HoaDonHoan, id=hh_id)
    
    if hh.trangthaiduyet == 'approved':
        # 1. Trừ lại tồn kho
        for item in hh.chitiet_hoan.all():
            if item.sanpham:
                item.sanpham.tonkho -= item.soluong
                item.sanpham.save()
        
        # 2. GHI ĐẢO NGƯỢC NỢ (chỉ khi đơn đã duyệt)
        khach = hh.khachhang
        last_entry = SoCaiCongNo.objects.filter(
            khachhang=khach
        ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
        
        no_hien_tai = Decimal(str(last_entry.du_no_tuc_thoi)) if last_entry else Decimal(str(khach.no_dau_ky))
        tang = Decimal(str(hh.tongtienhoan))
        no_moi = no_hien_tai + tang
        
        SoCaiCongNo.objects.create(
            khachhang=khach,
            ma_chung_tu=f"HUY-{hh.mahoadonhoan}",
            dien_giai=f"Hủy đơn hoàn {hh.mahoadonhoan}",
            tang=tang,
            giam=0,
            du_no_tuc_thoi=no_moi,
            user=request.user,
            ghichu="Hệ thống tự động điều chỉnh khi hủy đơn hoàn"
        )
            
    # 3. Cập nhật trạng thái
    hh.trangthaiduyet = 'canceled' 
    hh.save()
    
    return JsonResponse({
        'status': 'success', 
        'message': f'Đã hủy đơn hoàn {hh.mahoadonhoan}'
    })
@transaction.atomic
def edit_invoice_hoan(request, hh_id):
    """API sửa đơn hoàn PENDING"""
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    if not items_data or len(items_data) == 0:
        return JsonResponse({'status': 'error', 'message': 'Giỏ hàng trống, không thể lưu!'}, status=400)
    try:
        hh = HoaDonHoan.objects.select_for_update().get(id=hh_id)
        
        # Chỉ cho sửa đơn pending
        if hh.trangthaiduyet != 'pending':
            return JsonResponse({'status': 'error', 'message': 'Chỉ sửa được đơn chờ duyệt'}, status=400)
        
        data = json.loads(request.body)
        items_data = data.get('items', [])
        
        # Tính tổng tiền
        tong_tien_hang = Decimal('0')
        for item in items_data:
            gia = Decimal(str(item.get('gia', 0)))
            sl = Decimal(str(item.get('soluong', 1)))
            ck_phan_tram = Decimal(str(item.get('ck_item', 0)))
            
            tien_truoc_ck = gia * sl
            tien_chiet_khau = tien_truoc_ck * (ck_phan_tram / 100)
            thanh_tien = tien_truoc_ck - tien_chiet_khau
            tong_tien_hang += thanh_tien
        
        ck_tong = Decimal(str(data.get('chietkhau_tong') or 0))
        final_total = tong_tien_hang * (1 - ck_tong / 100)
        
        # Cập nhật hóa đơn
        hh.khachhang_id = data.get('khachhang_id')
        hh.ngaylap = datetime.strptime(data.get('ngay_lap'), '%Y-%m-%d').date() if data.get('ngay_lap') else hh.ngaylap
        hh.tongtienhoan = int(final_total)
        hh.lydohoan = data.get('ghichu_don', '')
        hh.save()
        
        # Xóa chi tiết cũ, tạo mới
        hh.chitiet_hoan.all().delete()
        
        for item in items_data:
            sp = SanPham.objects.get(id=int(item.get('id')))
            so_luong = Decimal(str(item.get('soluong') or 1))
            gia_ban = Decimal(str(item.get('gia') or 0))
            
            ck_phan_tram = Decimal(str(item.get('ck_item') or 0))
            tien_truoc_ck = so_luong * gia_ban
            tien_chiet_khau = tien_truoc_ck * (ck_phan_tram / 100)
            thanh_tien = tien_truoc_ck - tien_chiet_khau
            
            ChiTietHoaDonHoan.objects.create(
                hoadonhoan=hh,
                sanpham=sp,
                tensanpham=sp.tensanpham,
                donvitinh=item.get('donvi', sp.donvitinh),
                soluong=so_luong,
                dongiagoc=sp.dongiagoc,
                dongialucban=gia_ban,
                chietkhau=tien_chiet_khau,
                thanhtien=thanh_tien,
                ghichu=item.get('ghichu_sp', ''),
                user=request.user
            )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Đã cập nhật đơn hoàn {hh.mahoadonhoan}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
@transaction.atomic
def copy_invoice_hoan(request, hh_id):
    """API sao chép đơn hoàn đã duyệt - Trả về data để hiển thị trên POS"""
    try:
        hh_goc = get_object_or_404(HoaDonHoan, id=hh_id)
        
        # Chỉ cho copy đơn đã duyệt
        if hh_goc.trangthaiduyet != 'approved':
            return JsonResponse({'status': 'error', 'message': 'Chỉ copy đơn đã duyệt'}, status=400)
        
        # Lấy chi tiết để trả về
        items = []
        for ct in hh_goc.chitiet_hoan.all():
            tien_truoc_ck = float(ct.dongialucban * ct.soluong)
            ck_pt = (float(ct.chietkhau) / tien_truoc_ck * 100) if tien_truoc_ck > 0 else 0
            
            items.append({
                'id': ct.sanpham.id,
                'ten': ct.tensanpham,
                'gia': float(ct.dongialucban),
                'soluong': float(ct.soluong),
                'donvi': ct.donvitinh,
                'ck_item': round(ck_pt, 1),
                'ghichu_sp': ct.ghichu or ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'ma_goc': hh_goc.mahoadonhoan,
                'khachhang_id': hh_goc.khachhang.id if hh_goc.khachhang else None,
                'khachhang_ten': hh_goc.khachhang.tenkhachhang if hh_goc.khachhang else '',
                'items': items,
                'ghichu_don': f"Copy từ {hh_goc.mahoadonhoan}"
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)