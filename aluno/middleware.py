from types import SimpleNamespace

class SimpleUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')
        username = request.session.get('username')

        if user_id and username:
            # Cria um objeto simples para simular o user do Django
            request.user = SimpleNamespace(id=user_id, username=username, is_authenticated=True)
        else:
            # usuário anônimo
            request.user = SimpleNamespace(is_authenticated=False)

        response = self.get_response(request)
        return response