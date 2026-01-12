# app_quan_ly/decorators.py
"""
Decorators để kiểm tra quyền
"""
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages


def require_permission(permission_codename):
    """
    Yêu cầu permission cụ thể
    
    Ví dụ:
        @require_permission('approve_hoadonban')
        def approve_invoice(request, ma_hd):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'status': 'error', 'message': 'Chưa đăng nhập'}, status=401)
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            full_perm = f'app_quan_ly.{permission_codename}'
            if not request.user.has_perm(full_perm):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Bạn không có quyền {permission_codename}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_group(*group_names):
    """
    Yêu cầu thuộc group cụ thể
    
    Ví dụ:
        @require_group('Manager', 'Admin')
        def delete_customer(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'status': 'error', 'message': 'Chưa đăng nhập'}, status=401)
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            user_groups = request.user.groups.values_list('name', flat=True)
            if not any(g in user_groups for g in group_names):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Chỉ {", ".join(group_names)} mới có quyền'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Shortcuts
def staff_or_higher(view_func):
    """Yêu cầu ít nhất Staff"""
    return require_group('Staff', 'Manager', 'Admin')(view_func)


def manager_or_higher(view_func):
    """Yêu cầu Manager hoặc Admin"""
    return require_group('Manager', 'Admin')(view_func)


def admin_only(view_func):
    """Chỉ Admin (is_superuser)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, 'Chỉ Admin mới có quyền')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper
