from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def is_staff(user):
    """檢查使用者是否為 staff"""
    return user.is_authenticated and user.is_staff


def staff_required(view_func):
    """
    Staff 權限裝飾器
    
    Usage:
        @staff_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, '請先登入！')
            return redirect('mgmt_login')
        
        if not request.user.is_staff:
            print(f"Non-staff access attempt: {request.user.email}")
            messages.error(request, '您不是管理員，將您引導回首頁。')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper