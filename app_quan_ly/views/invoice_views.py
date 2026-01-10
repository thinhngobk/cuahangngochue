# views/invoice_views.py
from django.contrib import messages
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum
from django.core.paginator import Paginator
from app_quan_ly.models import (
    HoaDonBan, ChiTietHoaDonBan, SanPham, PhieuThu, SoCaiCongNo
)
from .helper_views import update_ledger
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
@transaction.atomic
def save_invoice(request):
    """
    ✅ API lưu/sửa hóa đơn bán hàng
    - Nếu có edit_id: SỬA đơn chưa duyệt
    - Nếu không: TẠO đơn mới
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Hết phiên'}, status=401)
    
    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        edit_id = data.get('edit_id')
        
        is_admin = request.user.has_perm('app_name.approve_hoadonban')
        is_approve_request = data.get('admin_approve', False)
        should_approve_now = is_admin and is_approve_request
        
        trang_thai_hd = 'approved' if should_approve_now else 'pending'
        trang_thai_pt = 'approved' if should_approve_now else 'pending'

        # ✅ 1. TẠO HOẶC SỬA HÓA ĐƠN
        if edit_id:
            # ✅ SỬA ĐƠN CHƯA DUYỆT
            hd = HoaDonBan.objects.select_for_update().get(id=edit_id)
            
            # ❌ NGĂN SỬA ĐƠN ĐÃ DUYỆT
            if hd.trangthaidon == 'approved':
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Hóa đơn {hd.mahoadonban} đã duyệt, không thể sửa!'
                }, status=400)
            
            # ✅ XÓA CHI TIẾT CŨ & PHIẾU THU CŨ (chưa duyệt)
            hd.chitiet_ban.all().delete()
            PhieuThu.objects.filter(
                mahoadon=hd.mahoadonban, 
                trang_thai_duyet='pending'
            ).delete()
            
            # Cập nhật khách hàng
            hd.khachhang_id = data.get('khachhang_id')
            hd.ngaylap = datetime.strptime(data.get('ngay_lap'), '%Y-%m-%d').date() if data.get('ngay_lap') else hd.ngaylap
        else:
            # ✅ TẠO ĐƠN MỚI

            hd = HoaDonBan.objects.create(
                khachhang_id=data.get('khachhang_id'), 
                ngaylap=datetime.strptime(data.get('ngay_lap'), '%Y-%m-%d').date() if data.get('ngay_lap') else date.today(),  # ← THÊM
                user=request.user
            )

        # 2. Lưu chi tiết & Tính tổng tiền
        tong_tien_hang = Decimal('0')
        for item in items_data:
            sp = SanPham.objects.get(id=int(item.get('id')))
            so_luong = Decimal(str(item.get('soluong') or 1))
            gia_ban = Decimal(str(item.get('gia') or 0))
            
            ck_phan_tram = Decimal(str(item.get('ck_item') or 0))
            tien_truoc_ck = so_luong * gia_ban
            tien_chiet_khau = tien_truoc_ck * (ck_phan_tram / 100)
            thanh_tien = tien_truoc_ck - tien_chiet_khau
            
            tong_tien_hang += thanh_tien

            ChiTietHoaDonBan.objects.create(
                hoadonban=hd, 
                sanpham=sp, 
                tensanpham=sp.tensanpham,
                donvitinh=item.get('donvi', sp.donvitinh), 
                soluong=so_luong, 
                dongiagoc=sp.dongiagoc, 
                dongiaban=gia_ban,
                chietkhau=tien_chiet_khau,
                thanhtien=thanh_tien,
                ghichu=item.get('ghichu_sp', ''),
                user=request.user
            )

        # 3. Áp dụng chiết khấu tổng đơn
        ck_tong = Decimal(str(data.get('chietkhau_tong') or 0))
        tong_sau_ck = tong_tien_hang * (1 - ck_tong / 100)
        
        # 4. Cập nhật thông tin hóa đơn
        hd.chietkhauchung = ck_tong
        hd.tongtienphaithanhtoan = int(tong_sau_ck)
        hd.khachhangungtien = Decimal(str(data.get('khachhangungtien') or 0))
        hd.trangthaidon = trang_thai_hd
        hd.ghichu = data.get('ghichu_don', '')
        hd.user = request.user
        hd.save()

        # 5. CHỈ trừ kho nếu Admin duyệt luôn
        if should_approve_now:
            for item in items_data:
                sp = SanPham.objects.get(id=int(item.get('id')))
                so_luong = Decimal(str(item.get('soluong') or 1))
                sp.tonkho -= so_luong
                sp.save()

        # 6. Tạo phiếu thu nếu khách trả tiền
        if hd.khachhangungtien > 0:
            PhieuThu.objects.create(
                khachhang=hd.khachhang,
                mahoadon=hd.mahoadonban,
                sotienthu=hd.khachhangungtien,
                hinhthucthanhtoan='Tiền mặt',
                user=request.user,
                trang_thai_duyet=trang_thai_pt,
                ghichu=f"Tiền ứng {'khi sửa' if edit_id else 'khi tạo'} đơn {hd.mahoadonban} - Đính kèm hóa đơn"
            )

        action_msg = 'sửa' if edit_id else 'tạo'
        return JsonResponse({
            'status': 'success', 
            'ma': hd.mahoadonban,
            'message': f'Đã {action_msg} và duyệt đơn hàng' if should_approve_now else f'Đã {action_msg} đơn chờ duyệt'
        })

    except HoaDonBan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy hóa đơn'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_invoice_for_edit_api(request, ma_hd):  # ← Đổi từ invoice_id sang ma_hd
    hd = get_object_or_404(HoaDonBan, mahoadonban=ma_hd)  # ← Đổi từ id sang mahoadonban
    
    if hd.trangthaidon != 'pending':
        return JsonResponse({
            'status': 'error',
            'message': f'Hóa đơn đã {hd.get_trangthaidon_display()}, không thể sửa!'
        }, status=403)
    
    chi_tiet = hd.chitiet_ban.all()
    cart_items = []
    
    for item in chi_tiet:
        tong_truoc_ck = float(item.soluong) * float(item.dongiaban)
        ck_pt = (float(item.chietkhau) / tong_truoc_ck * 100) if tong_truoc_ck > 0 else 0
        
        cart_items.append({
            'id': item.sanpham.id if item.sanpham else 0,
            'ten': item.tensanpham,
            'donvi': item.donvitinh or '',
            'soluong': float(item.soluong),
            'gia': float(item.dongiaban),
            'ck_item': round(ck_pt, 2),
            'ghichu_sp': item.ghichu or ''
        })
    
    return JsonResponse({
        'status': 'success',
        'data': {
            'edit_id': hd.id,
            'khachhang_id': hd.khachhang.id if hd.khachhang else None,
            'khachhang_ten': hd.khachhang.tenkhachhang if hd.khachhang else '',
            'chietkhau_tong': float(hd.chietkhauchung or 0),
            'khachhangungtien': float(hd.khachhangungtien or 0),
            'ghichu': hd.ghichu or '',
            'items': cart_items
        }
    })
def get_invoice_detail_api(request, ma_hd):
    """API lấy chi tiết hóa đơn"""
    try:
        hd = HoaDonBan.objects.filter(mahoadonban=ma_hd).first()
        if not hd:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy hóa đơn'}, status=404)

        # ✅ Khách trả = Tiền ứng (khachhangungtien)
        khach_da_tra = hd.khachhangungtien or Decimal('0')
        
        # ✅ Còn nợ = Tổng - Khách trả
        tong_tien = hd.tongtienphaithanhtoan or Decimal('0')
        con_no = tong_tien - khach_da_tra

        # Lấy chi tiết sản phẩm
        details = hd.chitiet_ban.all()
        item_list = []
        
        for i in details:
            gia = float(i.dongiaban or 0)
            sl = float(i.soluong or 0)
            tien_ck = float(i.chietkhau or 0)
            
            tong_truoc_ck = gia * sl
            phan_tram_ck = (tien_ck / tong_truoc_ck * 100) if tong_truoc_ck > 0 else 0
            
            item_list.append({
                'ten': i.tensanpham,
                'sl': sl,
                'dv': i.donvitinh or "-",
                'gia': gia,
                'ck_tien': tien_ck,
                'ck_pt': round(phan_tram_ck, 1),
                'thanh_tien': float(i.thanhtien or 0),
                'ghi_chu_dong': i.ghichu or ""
            })
        
        tong_cac_mon = sum(float(i.thanhtien or 0) for i in details)
        
        return JsonResponse({
            'status': 'success', 
            'data': {
                'id': hd.id,
                'ma_hd': hd.mahoadonban,
                'ngay': hd.ngaylap.strftime("%d/%m/%Y") if hd.ngaylap else (hd.ngaytao.strftime("%d/%m/%Y") if hd.ngaytao else ""),  # ← Ưu tiên ngaylap
                'khach': hd.khachhang.tenkhachhang if hd.khachhang else "Khách lẻ",
                'tam_tinh': tong_cac_mon, 
                'ck_tong_pt': float(hd.chietkhauchung or 0),
                'tong': float(tong_tien),
                'da_tt': float(khach_da_tra),  # ✅ Khách đã trả = Tiền ứng
                'con_no': float(con_no),       # ✅ Còn nợ = Tổng - Khách trả
                'trang_thai_don': hd.get_trangthaidon_display(),
                'slug_trang_thai': hd.trangthaidon,
                'ghichu': hd.ghichu or "",
                'items': item_list
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_invoices_api(request):
    """API lấy danh sách hóa đơn bán hàng"""
    try:
        ngay_loc = request.GET.get('date')
        ten_khach = request.GET.get('customer')
        tt_don = request.GET.get('status')
        page_number = request.GET.get('page', 1)
        page_size = 15

        hds = HoaDonBan.objects.select_related('khachhang').all().order_by('-ngaylap', '-ngaytao')  # ← Ưu tiên ngaylap
        if ngay_loc:
            hds = hds.filter(ngaylap=ngay_loc)  # ← Lọc theo ngaylap
        if ten_khach:
            hds = hds.filter(khachhang__tenkhachhang__icontains=ten_khach)
        if tt_don and tt_don != 'all':
            hds = hds.filter(trangthaidon=tt_don)

        paginator = Paginator(hds, page_size)
        page_obj = paginator.get_page(page_number)

        data_list = []
        for h in page_obj:
            tong_da_thu = PhieuThu.objects.filter(
                mahoadon=h.mahoadonban,
                trang_thai_duyet='approved'
            ).aggregate(total=Sum('sotienthu'))['total'] or 0

            data_list.append({
                'id': h.id,
                'ma_hd': h.mahoadonban,
                'ngay': h.ngaylap.strftime("%d/%m/%Y") if h.ngaylap else h.ngaytao.strftime("%d/%m/%Y"),  # ← Ưu tiên ngaylap
                'khach': h.khachhang.tenkhachhang if h.khachhang else "Khách lẻ",
                'tong': float(h.tongtienphaithanhtoan or 0),
                'da_tt': float(tong_da_thu),
                'con_no': float((h.tongtienphaithanhtoan or 0) - Decimal(str(tong_da_thu))),
                'trang_thai_don': h.get_trangthaidon_display(),
                'slug_status': h.trangthaidon,
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

@transaction.atomic
def approve_invoice(request, ma_hd):
    """API duyệt hóa đơn bán hàng"""
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}, status=405)
    
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Chỉ admin mới có quyền duyệt'}, status=403)
    
    try:
        with transaction.atomic():
            hd = HoaDonBan.objects.select_for_update().get(mahoadonban=ma_hd)
            
            if hd.trangthaidon == 'approved':
                return JsonResponse({'status': 'error', 'message': 'Hóa đơn này đã duyệt rồi'}, status=400)

            # Trừ kho
            for item in hd.chitiet_ban.all():
                sp = item.sanpham
                sp.tonkho -= item.soluong
                sp.save()

            # Duyệt hóa đơn → Signal tự ghi sổ TĂNG nợ
            hd.trangthaidon = 'approved'
            hd.save()

            # ✅ DUYỆT PHIẾU THU ĐI KÈM (nếu có)
            receipts = PhieuThu.objects.filter(
                mahoadon=hd.mahoadonban,
                trang_thai_duyet='pending'
            )
            for receipt in receipts:
                receipt.trang_thai_duyet = 'approved'
                receipt.save()
        from django.contrib import messages
        messages.success(request, f'✅ Đã duyệt đơn {hd.mahoadonban}')
        
        response = JsonResponse({
            'status': 'success',
            'message': f'✅ Đã duyệt đơn {hd.mahoadonban}',
            'new_status': hd.get_trangthaidon_display()
        })
        response['HX-Trigger'] = 'invoiceApproved'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
@transaction.atomic
def cancel_invoice(request, ma_hd):
    """API hủy hóa đơn"""
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}, status=405)
    
    try:
        invoice = get_object_or_404(HoaDonBan, mahoadonban=ma_hd)
        
        if invoice.trangthaidon == 'approved':
            # 1. Hoàn kho
            for item in invoice.chitiet_ban.all():
                if item.sanpham:
                    item.sanpham.tonkho += item.soluong
                    item.sanpham.save()
            
            # 2. Đảo ngược sổ hóa đơn
            if invoice.khachhang:
                khach = invoice.khachhang
                last_entry = SoCaiCongNo.objects.filter(
                    khachhang=khach
                ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
                
                no_hien_tai = Decimal(str(last_entry.du_no_tuc_thoi)) if last_entry else Decimal(str(khach.no_dau_ky))
                giam = Decimal(str(invoice.tongtienphaithanhtoan))
                no_moi = no_hien_tai - giam
                
                SoCaiCongNo.objects.create(
                    khachhang=khach,
                    ma_chung_tu=f"HUY-{invoice.mahoadonban}",
                    dien_giai=f"Hủy hóa đơn {invoice.mahoadonban}",
                    tang=0, giam=giam, du_no_tuc_thoi=no_moi,
                    user=request.user,
                    ghichu="Hệ thống tự động điều chỉnh khi hủy đơn"
                )
            
            # 3. Hủy phiếu thu
            phieu_thu = PhieuThu.objects.filter(mahoadon=invoice.mahoadonban).first()
            if phieu_thu and phieu_thu.trang_thai_duyet == 'approved':
                khach = phieu_thu.khachhang
                last_entry = SoCaiCongNo.objects.filter(
                    khachhang=khach
                ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
                
                no_hien_tai = Decimal(str(last_entry.du_no_tuc_thoi)) if last_entry else Decimal(str(khach.no_dau_ky))
                tang = Decimal(str(phieu_thu.sotienthu))
                no_moi = no_hien_tai + tang
                
                SoCaiCongNo.objects.create(
                    khachhang=khach,
                    ma_chung_tu=f"HUY-{phieu_thu.maphieuthu}",
                    dien_giai=f"Hủy phiếu thu {phieu_thu.maphieuthu}",
                    tang=tang, giam=0, du_no_tuc_thoi=no_moi,
                    user=request.user,
                    ghichu="Hệ thống tự động điều chỉnh khi hủy phiếu"
                )
                
                phieu_thu.trang_thai_duyet = 'canceled'
                phieu_thu.save()
        
        # ✅ 4. Dùng update() thay vì save() để bypass validation
        HoaDonBan.objects.filter(mahoadonban=ma_hd).update(trangthaidon='canceled')
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Đã hủy hóa đơn {ma_hd}'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
def copy_invoice(request, hd_id):
    """API sao chép hóa đơn đã duyệt"""
    try:
        hd_goc = get_object_or_404(HoaDonBan, id=hd_id)
        
        # Chỉ cho copy đơn đã duyệt
        if hd_goc.trangthaidon != 'approved':
            return JsonResponse({'status': 'error', 'message': 'Chỉ copy đơn đã duyệt'}, status=400)
        
        # Lấy chi tiết để trả về
        items = []
        for ct in hd_goc.chitiet_ban.all():
            tien_truoc_ck = float(ct.dongiaban * ct.soluong)
            ck_pt = (float(ct.chietkhau) / tien_truoc_ck * 100) if tien_truoc_ck > 0 else 0
            
            items.append({
                'id': ct.sanpham.id,
                'ten': ct.tensanpham,
                'gia': float(ct.dongiaban),
                'soluong': float(ct.soluong),
                'donvi': ct.donvitinh,
                'ck_item': round(ck_pt, 1),
                'ghichu_sp': ct.ghichu or ''
            })
        
        # Tính chiết khấu tổng đơn
        ck_tong = float(hd_goc.chietkhauchung or 0)
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'ma_goc': hd_goc.mahoadonban,
                'khachhang_id': hd_goc.khachhang.id if hd_goc.khachhang else None,
                'items': items,
                'chietkhau_tong': ck_tong,
                'ghichu_don': f"Copy từ {hd_goc.mahoadonban}"
            }
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
def print_invoice(request, ma_hd):
    """Trang in hóa đơn bán"""
    from app_quan_ly.templatetags.invoice_filters import number_to_words
    
    hoadon = get_object_or_404(HoaDonBan, mahoadonban=ma_hd)
    chitiet = hoadon.chitiet_ban.all()
    
    tam_tinh = sum(item.thanhtien for item in chitiet)
    tien_chiet_khau = tam_tinh * (hoadon.chietkhauchung / 100)
    con_no = hoadon.tongtienphaithanhtoan - (hoadon.khachhangungtien or 0)
    
    # Chuyển số thành chữ
    tien_bang_chu = number_to_words(hoadon.tongtienphaithanhtoan)
    
    return render(request, 'print_invoice.html', {
        'hoadon': hoadon,
        'chitiet': chitiet,
        'tam_tinh': tam_tinh,
        'tien_chiet_khau': tien_chiet_khau,
        'con_no': con_no,
        'tien_bang_chu': tien_bang_chu
    })
def print_invoice_hoan(request, ma_hd):
    """Trang in hóa đơn hoàn"""
    hoadon = get_object_or_404(HoaDonHoan, mahoadonhoan=ma_hd)
    chitiet = hoadon.chitiet_hoan.all()
    
    tam_tinh = sum(item.thanhtien for item in chitiet)
    tien_chiet_khau = tam_tinh * (hoadon.chietkhauchung / 100)
    
    return render(request, 'print_invoice_hoan.html', {
        'hoadon': hoadon,
        'chitiet': chitiet,
        'tam_tinh': tam_tinh,
        'tien_chiet_khau': tien_chiet_khau
    })