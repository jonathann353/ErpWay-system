from django.shortcuts import redirect

def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if getattr(request.user, 'is_authenticated', False):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper