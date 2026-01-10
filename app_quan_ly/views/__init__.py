# views/__init__.py


# Trang HTML
from .page_views import (
    index_view,
    pos_view,
    pos_hoan_view,
    invoice_manager_view,
    invoice_hoan_manager_view,
)

# Sản phẩm
from .product_views import (
    search_san_pham,
    add_product_fast,
    product_manager,
)

# Khách hàng
from .customer_views import (
    add_customer_fast,
    customer_manager, 
)

# Hóa đơn bán
from .invoice_views import (
    save_invoice,
    get_invoice_for_edit_api,
    get_invoice_detail_api,
    get_invoices_api,
    approve_invoice,
    cancel_invoice,
)

# Hóa đơn hoàn
from .return_views import (
    save_invoice_hoan,
    get_invoices_hoan_api,
    get_invoice_hoan_detail_api,
    approve_invoice_hoan,
    cancel_invoice_hoan,
)

# Phiếu thu
from .receipt_views import (
    save_receipt,
    danh_sach_phieu_thu,    
    luu_phieu_thu_nhanh,
    huy_phieu_thu,
    duyet_phieu_thu,
)

# Sổ cái
from .ledger_views import (
    get_customer_ledger_api,
    api_so_chi_tiet_no,
    xem_so_cai,
    update_ghi_chu_so_cai,
)

# Helper
from .helper_views import update_ledger

__all__ = [
    # Pages
    'index_view',
    'pos_view',
    'pos_hoan_view',
    'invoice_manager_view',
    'invoice_hoan_manager_view',
    
    # Products
    'search_san_pham',
    'add_product_fast',
    'product_manager',
    
    # Customers
    'add_customer_fast',
    'customer_manager',
    
    # Invoices
    'save_invoice',
    'get_invoice_for_edit',
    'get_invoice_detail_api',
    'get_invoices_api',
    'approve_invoice',
    'cancel_invoice',
    
    # Returns
    'save_invoice_hoan',
    'get_invoices_hoan_api',
    'get_invoice_hoan_detail_api',
    'approve_invoice_hoan',
    'cancel_invoice_hoan',
    
    # Receipts
    'save_receipt',
    'danh_sach_phieu_thu',
    'post_phieu_thu',
    'luu_phieu_thu_nhanh',
    'huy_phieu_thu',
    'duyet_phieu_thu',
    
    # Ledger
    'get_customer_ledger_api',
    'api_so_chi_tiet_no',
    'xem_so_cai',
    'update_ghi_chu_so_cai',
    
    # Helpers
    'update_ledger',
]