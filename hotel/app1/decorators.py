from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def group_required(group_name):
    """
    Only allow users in given group (or superusers).
    If not, show friendly message instead of 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            return render(request, "no_access.html", {"page": request.path})
        return _wrapped_view
    return decorator
