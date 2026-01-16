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
import pandas as pd
from django.contrib import messages
from django.core.paginator import Paginator

def product_manager(request):
    products = SanPham.objects.filter(user=request.user).order_by('-ngaycapnhat')
    
    # Phân trang 50 sản phẩm/trang
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    products_list = SanPham.objects.filter(user=request.user).order_by('-ngaycapnhat')
    products_data = [{
        'id': p.id,
        'ma': p.masanpham,
        'ten': p.tensanpham,
        'ten_khong_dau': p.tensanphamkhongdau,
        'barcode': p.barcode or '',
        'donvi': p.donvitinh,
        'gia_goc': float(p.dongiagoc),
        'gia_ban': float(p.dongiaban),
        'ton_kho': p.tonkho,
        'ghichu': p.ghichu or '',
        'is_active': p.is_active
    } for p in page_obj]
    
    context = {
        'products_json': json.dumps(products_data, ensure_ascii=False),
        'page_obj': page_obj,
        'total_products': paginator.count
    }
    return render(request, 'product_manager.html', context)
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
            @click.prevent="
                selectedProduct = {{
                    id: {sp.id}, 
                    ma: '{sp.masanpham}', 
                    ten: '{ten_sp_safe}', 
                    gia: {float(sp.dongiaban)}, 
                    gia_goc: {float(sp.dongiagoc)},
                    donvi: '{dvt}',
                    ton: {sp.tonkho}
                }}; 
                productSearch = '{ten_sp_safe}'; 
                document.getElementById('search-results').innerHTML = '';
                setTimeout(() => {{
                    let inp = document.querySelector('input[x-ref=qtyInput]');
                    if(inp) {{ inp.focus(); inp.select(); }}
                }}, 150);
            ">
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
            barcode = data.get('barcode', '').strip() or ''
            gia_goc = Decimal(str(data.get('gia_goc', 0)))
            gia_ban = Decimal(str(data.get('gia_ban', 0)))  # ← SỬA: 'gia' thành 'gia_ban'
            donvi = data.get('donvi', 'Cái').strip()
            tonkho = int(data.get('ton_kho', 0))  # ← SỬA: 'tonkho' thành 'ton_kho'
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
                'product': {
                    'id': sp.id,
                    'ma': sp.masanpham,
                    'ten': sp.tensanpham,
                    'barcode': sp.barcode,
                    'donvi': sp.donvitinh,
                    'gia_goc': float(sp.dongiagoc),
                    'gia_ban': float(sp.dongiaban),
                    'ton_kho': sp.tonkho,
                    'is_active': sp.is_active,
                    'ghichu': sp.ghichu
                },
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
def get_products_api(request):
    """Lấy danh sách tất cả sản phẩm"""
    products = SanPham.objects.all().order_by('-id')
    data = [{
        'id': p.id,
        'ma': p.masanpham,
        'ten': p.tensanpham,
        'barcode': p.barcode or '',
        'donvi': p.donvitinh,
        'gia_goc': float(p.dongiagoc),
        'gia_ban': float(p.dongiaban),
        'ton_kho': p.tonkho,
        'is_active': p.is_active,
        'ghichu': p.ghichu or ''
    } for p in products]
    return JsonResponse(data, safe=False)

def update_product_api(request, product_id):
    """Cập nhật sản phẩm"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product = SanPham.objects.get(id=product_id)
            
            product.tensanpham = data.get('ten', '').strip()
            product.barcode = data.get('barcode', '').strip() or ''
            product.donvitinh = data.get('donvi', 'Cái').strip()
            product.dongiagoc = Decimal(str(data.get('gia_goc', 0)))
            product.dongiaban = Decimal(str(data.get('gia_ban', 0)))
            product.tonkho = int(data.get('ton_kho', 0))
            product.is_active = data.get('is_active', True)
            product.ghichu = data.get('ghichu', '').strip()
            product.save()
            
            return JsonResponse({'status': 'success', 'message': 'Cập nhật thành công'})
        except SanPham.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sản phẩm không tồn tại'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def toggle_product_status(request, product_id):
    """Bật/tắt trạng thái sản phẩm"""
    if request.method == 'POST':
        try:
            product = SanPham.objects.get(id=product_id)
            product.is_active = not product.is_active
            product.save()
            return JsonResponse({
                'status': 'success', 
                'message': f'Đã {"kích hoạt" if product.is_active else "ngừng bán"} sản phẩm',
                'is_active': product.is_active
            })
        except SanPham.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sản phẩm không tồn tại'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
def import_products(request):
    if request.method != 'POST':
        return redirect('product_manager')
    
    excel_file = request.FILES.get('excel_file')
    if not excel_file:
        messages.error(request, 'Vui lòng chọn file Excel')
        return redirect('product_manager')
    
    try:
        # Đọc file Excel
        df = pd.read_excel(excel_file)
        
        # Kiểm tra columns (dùng tên cột từ model)
        required_cols = ['tensanpham', 'donvitinh', 'dongiagoc', 'dongiaban']
        if not all(col in df.columns for col in required_cols):
            messages.error(request, f'File Excel thiếu các cột bắt buộc: {", ".join(required_cols)}')
            return redirect('product_manager')
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for _, row in df.iterrows():
                tensanpham = str(row['tensanpham']).strip()
                donvitinh = str(row['donvitinh']).strip()
                dongiagoc = float(row['dongiagoc'])
                dongiaban = float(row['dongiaban'])
                tonkho = int(row.get('tonkho', 0)) if 'tonkho' in df.columns and pd.notna(row.get('tonkho')) else 0
                barcode = str(row.get('barcode', '')).strip() if 'barcode' in df.columns and pd.notna(row.get('barcode')) else ''
                ghichu = str(row.get('ghichu', '')).strip() if 'ghichu' in df.columns and pd.notna(row.get('ghichu')) else ''
                
                # Tạo tên không dấu
                from unidecode import unidecode
                tensanphamkhongdau = unidecode(tensanpham).lower()
                
                # Tìm sản phẩm trùng
                existing = SanPham.objects.filter(
                    tensanphamkhongdau=tensanphamkhongdau,
                    donvitinh=donvitinh
                ).first()
                
                if existing:
                    # Cập nhật giá
                    existing.dongiagoc = dongiagoc
                    existing.dongiaban = dongiaban
                    if tonkho:
                        existing.tonkho = tonkho
                    if barcode:
                        existing.barcode = barcode
                    if ghichu:
                        existing.ghichu = ghichu
                    existing.save()
                    updated_count += 1
                else:
                    # Tạo mới
                    SanPham.objects.create(
                        tensanpham=tensanpham,
                        tensanphamkhongdau=tensanphamkhongdau,
                        donvitinh=donvitinh,
                        dongiagoc=dongiagoc,
                        dongiaban=dongiaban,
                        tonkho=tonkho,
                        barcode=barcode,
                        ghichu=ghichu,
                        user=request.user
                    )
                    created_count += 1
        
        messages.success(request, f'✅ Import thành công: {created_count} sản phẩm mới, {updated_count} sản phẩm cập nhật')
        
    except Exception as e:
        messages.error(request, f'❌ Lỗi import: {str(e)}')
    
    return redirect('product_manager')