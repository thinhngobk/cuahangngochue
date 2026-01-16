from django.contrib import admin
from django.urls import path, include
import os
from app_quan_ly import views 
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from app_quan_ly.views import invoice_views, return_views,customer_views, product_views  # ← Thêm return_views

urlpatterns = [
    # --- ĐIỀU HƯỚNG TRANG CHỦ ---
    path('', views.index_view, name='index'),
    
    # --- HỆ THỐNG ĐĂNG NHẬP / ĐĂNG XUẤT ---
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('admin/', admin.site.urls),

    # --- GIAO DIỆN CHÍNH ---
    path('pos/', login_required(views.pos_view), name='pos'), 
    path('hoa-don/', login_required(views.invoice_manager_view), name='invoice_manager'),
    path('danh-sach-phieu-thu/', login_required(views.danh_sach_phieu_thu), name='danh_sach_phieu_thu'),
    path('so-cai-cong-no/', login_required(views.xem_so_cai), name='so_cai_cong_no'),

    # --- API XỬ LÝ DỮ LIỆU ---
    # Hóa đơn
    path('api/get-invoices/', login_required(views.get_invoices_api), name='get_invoices_api'),
    path('api/get-invoice-detail/<str:ma_hd>/', login_required(views.get_invoice_detail_api), name='get_invoice_detail_api'),
    path('api/save-invoice/', login_required(views.save_invoice), name='save_invoice'),
    path('api/get-invoice-for-edit/<str:ma_hd>/', invoice_views.get_invoice_for_edit_api, name='get_invoice_for_edit'),
    path('approve-invoice/<str:ma_hd>/', login_required(invoice_views.approve_invoice), name='approve_invoice'),
    path('cancel-invoice/<str:ma_hd>/', login_required(invoice_views.cancel_invoice), name='cancel_invoice'),
    path('print-invoice/<str:ma_hd>/', login_required(invoice_views.print_invoice), name='print_invoice'),
    path('api/copy-invoice/<int:hd_id>/', login_required(invoice_views.copy_invoice), name='copy_invoice'),
    
    # Sản phẩm & Khách hàng
    path('search-sp/', login_required(views.search_san_pham), name='search_sp'),
    path('add_customer_fast/', login_required(views.add_customer_fast), name='add_customer_fast'),
    path('add_product_fast/', login_required(views.add_product_fast), name='add_product_fast'),
    path('customer-manager/', login_required(views.customer_manager), name='customer_manager'),
    path('product-manager/', login_required(views.product_manager), name='product_manager'),
    path('products/', login_required(views.product_manager), name='products'),  # Thêm alias
    path('api/get-customers/', login_required(customer_views.get_customers_api), name='get_customers_api'),
    path('api/customer-detail/<int:kh_id>/', login_required(customer_views.get_customer_detail_api), name='customer_detail_api'),
    path('api/update-customer/<int:kh_id>/', login_required(customer_views.update_customer_api), name='update_customer_api'),
    # API Sản phẩm
    path('api/get-products/', login_required(product_views.get_products_api), name='get_products_api'),
    path('api/update-product/<int:product_id>/', login_required(product_views.update_product_api), name='update_product_api'),
    path('api/toggle-product-status/<int:product_id>/', login_required(product_views.toggle_product_status), name='toggle_product_status'),
    path('api/search-customers/', login_required(customer_views.search_customers_api), name='search_customers_api'),
        

    # Phiếu thu & Công nợ
    path('api/save-receipt/', login_required(views.save_receipt), name='save_receipt'),
    path('luu-phieu-thu-nhanh/', login_required(views.luu_phieu_thu_nhanh), name='luu_phieu_thu_nhanh'),
    path('duyet-phieu-thu/<int:pk>/', login_required(views.duyet_phieu_thu), name='duyet_phieu_thu'),
    path('huy-phieu-thu/<int:pk>/', login_required(views.huy_phieu_thu), name='huy_phieu_thu'),
    path('update-ghi-chu-so-cai/', login_required(views.update_ghi_chu_so_cai), name='update_ghi_chu_so_cai'),
    
    # === HOÀN HÀNG ===
    path('pos-hoan/', login_required(views.pos_hoan_view), name='pos_hoan'),
    path('hoa-don-hoan/', login_required(views.invoice_hoan_manager_view), name='invoice_hoan_manager'),
    
    # API Hoàn hàng
    path('api/save-invoice-hoan/', login_required(return_views.save_invoice_hoan), name='save_invoice_hoan'),
    path('api/invoices-hoan/', login_required(return_views.get_invoices_hoan_api), name='get_invoices_hoan_api'),
    path('api/invoice-hoan-detail/<str:ma_hd>/', login_required(return_views.get_invoice_hoan_detail_api), name='get_invoice_hoan_detail'),
    path('api/approve-invoice-hoan/<int:hh_id>/', login_required(return_views.approve_invoice_hoan), name='approve_invoice_hoan'),
    path('api/cancel-invoice-hoan/<int:hh_id>/', login_required(return_views.cancel_invoice_hoan), name='cancel_invoice_hoan'),  # ← Sửa id → hh_id
    path('api/copy-invoice-hoan/<int:hh_id>/', login_required(return_views.copy_invoice_hoan), name='copy_invoice_hoan'),  # ← Thêm login_required
    path('api/hoan/edit/<int:hh_id>/', return_views.edit_invoice_hoan, name='edit_invoice_hoan'),
    
]
if settings.DEBUG:
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    
    # Static files
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))