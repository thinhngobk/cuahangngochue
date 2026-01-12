# views/product_views.py
"""
API liên quan đến Sản phẩm
"""
import json
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q, Case, When, Value, IntegerField
from unidecode import unidecode
from app_quan_ly.models import SanPham
from django.shortcuts import render
def product_manager(request):
    """Trang quản lý sản phẩm"""
    return render(request, 'product_manager.html')
def search_san_pham(request):
    """
    Tìm kiếm sản phẩm TỐI ƯU cho 4000 SP
    Ưu tiên: 1. Tên bắt đầu → 2. Tên chứa → 3. Mã SP
    """
    q = request.GET.get('q', '').strip()
    
    # ✅ YÊU CẦU TỐI THIỂU 2 KÝ TỰ (giảm load server)
    if not q or len(q) < 2:
        return HttpResponse("")
    
    q_khong_dau = unidecode(q).lower()
    q_upper = q.upper()
    
    # ========================================
    # TÌM KIẾM CÓ PRIORITY RANKING
    # ========================================
    
    results = SanPham.objects.filter(
        Q(tensanphamkhongdau__startswith=q_khong_dau) |  # 1. Tên bắt đầu
        Q(tensanphamkhongdau__icontains=q_khong_dau) |   # 2. Tên chứa
        Q(masanpham__icontains=q_upper) |                 # 3. Mã SP
        Q(barcode__icontains=q),                          # 4. Barcode
        is_active=True
    ).annotate(
        # Xếp hạng theo độ ưu tiên
        priority=Case(
            When(tensanphamkhongdau__startswith=q_khong_dau, then=Value(1)),  # Tên bắt đầu
            When(tensanphamkhongdau__icontains=q_khong_dau, then=Value(2)),   # Tên chứa
            When(masanpham__iexact=q_upper, then=Value(3)),                   # Mã exact
            When(barcode__iexact=q, then=Value(3)),                           # Barcode exact
            When(masanpham__icontains=q_upper, then=Value(4)),                # Mã chứa
            When(barcode__icontains=q, then=Value(5)),                        # Barcode chứa
            default=Value(6),
            output_field=IntegerField(),
        )
    ).select_related().order_by('priority', 'tensanpham')[:10]
    
    # ========================================
    # RENDER HTML
    # ========================================
    html = ""
    for idx, sp in enumerate(results):
        dvt = sp.donvitinh or 'Cái'
        ten_sp_safe = sp.tensanpham.replace("'", "\\'")
        
        # Highlight top result (priority = 1)
        is_top = sp.priority == 1
        border_class = "border-l-4 border-emerald-500 bg-emerald-50" if is_top else ""
        
        # Badge cho kết quả đầu tiên
        badge = ""
        if idx == 0 and is_top:
            badge = '<span class="px-2 py-1 bg-emerald-500 text-white text-xs font-bold rounded ml-2">TOP</span>'
        
        html += f"""
        <div class="p-3 hover:bg-blue-50 cursor-pointer border-b {border_class} flex items-center space-x-4 transition-colors" 
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
                <div class="font-bold {'text-emerald-900' if is_top else 'text-blue-900'}">{sp.tensanpham} {badge}</div>
                <div class="text-xs text-gray-500">
                    Mã: {sp.masanpham} 
                    {f'| Barcode: {sp.barcode}' if sp.barcode else ''} 
                    | Tồn: <span class="{'text-emerald-600 font-bold' if sp.tonkho > 10 else 'text-orange-600'}">{sp.tonkho}</span>
                </div>
            </div>
            <div class="text-right">
                <div class="text-red-600 font-extrabold text-lg">{int(sp.dongiaban):,}₫</div>
                <div class="text-xs text-gray-400">Gốc: {int(sp.dongiagoc):,}₫</div>
            </div>
        </div>
        """
    
    # Nếu không tìm thấy gì
    if not html:
        html = """
        <div class="p-6 text-center text-gray-400">
            <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="font-bold">Không tìm thấy sản phẩm</div>
            <div class="text-xs mt-1">Thử từ khóa khác hoặc kiểm tra chính tả</div>
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