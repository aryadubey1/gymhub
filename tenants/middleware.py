import threading

_thread_locals = threading.local()

def get_current_gym():
    return getattr(_thread_locals, 'gym', None)

def set_current_gym(gym):
    _thread_locals.gym = gym

class CurrentGymMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        gym = None
        if request.user.is_authenticated:
            gym = getattr(request.user, 'gym', None)
        set_current_gym(gym)

        try:
            response = self.get_response(request)
        finally:
            set_current_gym(None)
        return response