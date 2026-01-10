# views/product_views.py
"""
API liên quan đến Sản phẩm
"""
import json
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q
from unidecode import unidecode
from app_quan_ly.models import SanPham
from django.shortcuts import render
def product_manager(request):
    """Trang quản lý sản phẩm"""
    return render(request, 'product_manager.html')
def search_san_pham(request):
    """Tìm kiếm sản phẩm cho POS"""
    q = request.GET.get('q', '').strip()
    if not q:
        return HttpResponse("")
    
    q_khong_dau = unidecode(q).lower()
    sps = SanPham.objects.filter(
        Q(tensanpham__icontains=q) | 
        Q(tensanphamkhongdau__icontains=q_khong_dau) |
        Q(masanpham__icontains=q) |
        Q(barcode__icontains=q)
    )[:10]

    html = ""
    for sp in sps:
        dvt = sp.donvitinh or 'Cái'
        ten_sp_safe = sp.tensanpham.replace("'", "\\'") 
        
        html += f"""
        <div class="p-3 hover:bg-blue-50 cursor-pointer border-b flex items-center space-x-4 transition-colors" 
            @click="selectedProduct = {{
                id: {sp.id}, 
                ma: '{sp.masanpham}', 
                ten: '{ten_sp_safe}', 
                gia: {float(sp.dongiaban)}, 
                gia_goc: {float(sp.dongiagoc)},
                donvi: '{dvt}',
                ton: {sp.tonkho}
            }}; 
            searchProdQuery = '{ten_sp_safe}'; 
            $nextTick(() => $refs.qtyInput?.focus())">
            <div class="flex-1">
                <div class="font-bold text-blue-900">{sp.tensanpham}</div>
                <div class="text-xs text-gray-500">Mã: {sp.masanpham} | Tồn: <span class="text-orange-600">{sp.tonkho}</span></div>
            </div>
            <div class="text-right">
                <div class="text-red-600 font-extrabold">{int(sp.dongiaban):,}đ</div>
            </div>
        </div>
        """
    return HttpResponse(html)


@transaction.atomic
def add_product_fast(request):
    """API thêm nhanh sản phẩm với đầy đủ thông tin"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate dữ liệu bắt buộc
            ten = data.get('ten', '').strip()
            if not ten:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Tên sản phẩm không được để trống'
                }, status=400)
            
            # Lấy và xử lý dữ liệu
            barcode = data.get('barcode', '').strip()
            gia_goc = Decimal(str(data.get('gia_goc', 0)))
            gia_ban = Decimal(str(data.get('gia', 0)))
            donvi = data.get('donvi', 'Cái').strip()
            tonkho = int(data.get('tonkho', 0))
            ghichu = data.get('ghichu', '').strip()
            
            # Tạo sản phẩm mới
            sp = SanPham.objects.create(
                tensanpham=ten,
                barcode=barcode,
                dongiagoc=gia_goc,
                dongiaban=gia_ban,
                donvitinh=donvi,
                tonkho=tonkho,
                ghichu=ghichu,
                user=request.user,
                is_active=True
            )
            
            return JsonResponse({
                'status': 'success', 
                'id': sp.id, 
                'ten': sp.tensanpham,
                'gia': float(sp.dongiaban),
                'donvi': sp.donvitinh,
                'message': f'Đã thêm sản phẩm: {sp.tensanpham}'
            })
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Dữ liệu không hợp lệ: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Lỗi hệ thống: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Phương thức không hợp lệ'
    }, status=405)