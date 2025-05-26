import datetime
import requests
import hashlib
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from supabase import create_client, Client
from .decorators import login_required_custom
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


url = "https://pgdldfqzqgxowqedrldh.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnZGxkZnF6cWd4b3dxZWRybGRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1Nzk0MjksImV4cCI6MjA1MzE1NTQyOX0.jntDjoG90UW916FljiMlrmM4YqaNLeTphwTO2IPkY9E"
supabase: Client = create_client(url, key)

# Create your views here.
@login_required_custom
def Aluno(request):
    try:
        # Requisição GET para a API externa que lista os alunos
        response = requests.get('https://api-flask-academia.onrender.com/listar/aluno')

        if response.status_code == 200:
            alunos = response.json().get('dados', [])
        else:
            alunos = []
            error_message = response.json().get('message', 'Erro desconhecido')
            messages.error(request, f"Erro ao buscar alunos: {error_message}")

    except requests.exceptions.RequestException as e:
        alunos = []
        messages.error(request, f"Erro de conexão com a API: {str(e)}")

    # Passa alunos para o template
    return render(request, 'aluno/aluno.html', {'alunos': alunos})

def editar_aluno(request, cod_aluno):
    if request.method == "POST":
        cod_aluno = request.POST.get("cod_aluno")
        dados = {
            "nome": request.POST.get("nome"),
            "cpf": request.POST.get("cpf"),
            "email": request.POST.get("email"),
            "telefone": request.POST.get("telefone"),
            "status": request.POST.get("status") == 'on',
            "cod_instrutor": request.POST.get("cod_instrutor")
        }

        response = supabase.table("alunos").update(dados).eq("cod_aluno", cod_aluno).execute()
        return redirect(reverse('aluno'))
def perfil(request, cod_aluno):
    # exemplo simplificado para testes
    aluno = {
        'foto_url': '/static/img/avatar.png',
        'nome': 'João da Silva',
        'cpf': '123.456.789-00',
        'email': 'joao@email.com',
        'telefone': '(51) 99999-9999',
        'sexo': 'Masculino',
        'data_nascimento': '1990-01-01',
        'status': 'Ativo',
        'cod_instrutor': '45',
        'nome_instrutor': 'Carlos Treinador'
    }

    # Dados mockados para outras seções
    contexto = {
        'aluno': aluno,
        'treino': {
            'nome': 'Hipertrofia A-B',
            'inicio': '2025-05-01',
            'fim': '2025-06-01',
            'exercicios': {
                'Peito': ['Supino reto', 'Crucifixo'],
                'Pernas': ['Agachamento livre', 'Leg press']
            },
            'ficha_url': '#'
        },
        'historico': [],
        'pagamento': {
            'status': 'Pago',
            'vencimento': '2025-05-10',
            'forma': 'Pix',
            'valor': 149.90
        },
        'historico_pagamentos': [],
        'avaliacao': {
            'data': '2025-04-15',
            'peso': 78,
            'altura': 1.75,
            'imc': 25.5,
            'observacoes': 'Boa evolução nos últimos 3 meses.'
        },
        'documentos': [
            {'nome': 'Contrato de matrícula', 'url': '#'}
        ]
    }

    return render(request, 'aluno/perfil.html', contexto)

def treinos_peito(request):
    url = "https://exercise-db-fitness-workout-gym.p.rapidapi.com/exercises"
    headers = {
        "x-rapidapi-key": "SUA_CHAVE_AQUI",
        "x-rapidapi-host": "exercise-db-fitness-workout-gym.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    try:
        data = response.json()
    except ValueError:
        data = []  # falha no JSON, deixa vazio

    # Verifica se data é lista, se não é tenta extrair lista de dentro do dict
    if isinstance(data, dict):
        # exemplo: {'exercises': [...] } ou {'message': 'error'}
        if "exercises" in data:
            exercicios = data["exercises"]
        else:
            exercicios = []
    elif isinstance(data, list):
        exercicios = data
    else:
        exercicios = []

    selected = request.GET.get('exercicio', '')

    if selected:
        exercicios_filtrados = [e for e in exercicios if selected.lower() in e.get('name', '').lower()]
    else:
        exercicios_filtrados = exercicios

    context = {
        'exercicios': exercicios,
        'treinos': exercicios_filtrados,
        'selected': selected,
    }
    return render(request, "aluno/treinos_peito.html", context)

@csrf_exempt
def cadastrar_aluno(request):
    if request.method == 'POST':
        aluno = {
            'nome': request.POST.get('nome'),
            'cpf': request.POST.get('cpf'),
            'email': request.POST.get('email'),
            'telefone': request.POST.get('telefone'),
            'Cod_instrutor': request.POST.get('Cod_instrutor'),
            'status': request.POST.get('status') == 'True',
            'data_nascimento': request.POST.get('data_nascimento'),
            'sexo': request.POST.get('sexo'),
        }

        try:
            response = requests.post('https://api-flask-academia.onrender.com/inserir/aluno', json=aluno)
            if response.status_code == 201:
                messages.success(request, 'Aluno cadastrado com sucesso!')
            else:
                messages.error(request, f'Erro ao cadastrar aluno: {response.json().get("message", "Erro desconhecido")}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Erro ao conectar com a API: {str(e)}')

    return redirect('dashboard')

@login_required_custom
def dashboard(request):
    # --- Consulta de alunos ---
    try:
        response = requests.get('https://api-flask-academia.onrender.com/listar/aluno')

        if response.status_code == 200:
            dados_api = response.json().get('dados', [])
            alunos = []

            for aluno in dados_api:
                status = 'Ativo' if aluno.get('ativo', False) else 'Inativo'
                aluno['status'] = status
                alunos.append(aluno)
        else:
            alunos = []
            error_message = response.json().get('message', 'Erro desconhecido')
            messages.error(request, f"Erro ao buscar alunos: {error_message}")

    except requests.exceptions.RequestException as e:
        alunos = []
        messages.error(request, f"Erro de conexão com a API: {str(e)}")

    total_alunos = len(alunos)

    # --- Consulta de instrutores ---
    try:
        response_instrutor = requests.get('https://api-flask-academia.onrender.com/listar/instrutor')

        if response_instrutor.status_code == 200:
            dados_instrutor = response_instrutor.json().get('dados', [])
            instrutores = []

            for instrutor in dados_instrutor:
                status = 'Ativo' if instrutor.get('ativo', False) else 'Inativo'
                instrutor['status'] = status
                instrutores.append(instrutor)
        else:
            instrutores = []
            error_message = response_instrutor.json().get('message', 'Erro desconhecido')
            messages.error(request, f"Erro ao buscar instrutores: {error_message}")

    except requests.exceptions.RequestException as e:
        instrutores = []
        messages.error(request, f"Erro de conexão com a API (instrutores): {str(e)}")

    total_instrutores = len(instrutores)

    # --- Consulta de pagamentos no Supabase ---
    try:
        pagamentos = supabase.table("pagamento").select("valor, data_pagamento").execute()
        dados_pagamentos = pagamentos.data or []

        soma_valores = sum(item.get('valor', 0) for item in dados_pagamentos)
        ultimo_pagamento = max(dados_pagamentos, key=lambda x: x.get('data_pagamento'), default=None)
        ultimo_valor_pago = ultimo_pagamento.get('valor', 0) if ultimo_pagamento else 0

    except Exception as e:
        soma_valores = 0
        ultimo_valor_pago = 0
        messages.error(request, f"Erro ao consultar pagamentos no Supabase: {str(e)}")

    return render(request, 'aluno/dashboard.html', {
        'alunos': alunos,
        'total_alunos': total_alunos,
        'instrutores': instrutores,
        'total_instrutores': total_instrutores,
        'soma_valores': soma_valores,
        'ultimo_pagamento': ultimo_valor_pago
    })


    
def buscar_global(request):
    q = request.GET.get('q', '')
    resultados = Aluno.objects.filter(
        q(nome__icontains=q) | q(cpf__icontains=q) | q(email__icontains=q)
    )
    return render(request, 'resultados_busca.html', {'resultados': resultados})

def filtrar_alunos(request):
    status = request.GET.get('status')
    

    alunos = Aluno.objects.all()

    if status:
        alunos = alunos.filter(status=status)

    return render(request, 'alunos_filtrados.html', {'alunos': alunos})

    
def logout_view(request):
    request.session.flush()
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Gerar hash da senha fornecida
        hashed_input_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        try:
            # Consulta no Supabase
            response = supabase.table("auth_user").select("*").eq("username", username).execute()
            user_data = response.data

            if user_data:
                user = user_data[0]
                stored_password_hash = user['password']

                if hashed_input_password == stored_password_hash:
                    # Salvar dados na sessão
                    request.session['username'] = user['username']
                    request.session['user_id'] = user['id']

                    # Verificar se é superusuário
                    if user.get('is_superuser', False):
                        return redirect('dashboard')  # redireciona para o dashboard
                    else:
                        return redirect('aluno')  # redireciona para a página do aluno
                else:
                    return render(request, 'accounts/login.html', {'error': 'Usuário ou senha incorretos.'})
            else:
                return render(request, 'accounts/login.html', {'error': 'Usuário não encontrado.'})

        except Exception as e:
            return render(request, 'accounts/login.html', {'error': f'Erro no login: {str(e)}'})

    return render(request, 'accounts/login.html')

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "As senhas não coincidem.")
            return render(request, "accounts/register.html")

        data = {
            "username": username,
            "email": email,
            "password": password1
        }

        try:
            response = requests.post("https://api-flask-academia.onrender.com/register", json=data)

            if response.status_code == 201:
                messages.success(request, "Registro realizado com sucesso! Faça login.")
                return redirect("accounts/login")
            else:
                messages.error(request, "Erro ao registrar. Verifique os dados ou tente novamente.")
        except requests.exceptions.RequestException:
            messages.error(request, "Erro ao conectar com o servidor de registro. Tente novamente mais tarde.")

    return render(request, "accounts/register.html")

def listar_instrutores(request):
    try:
        response = requests.get('https://api-flask-academia.onrender.com/listar/instrutor')

        if response.status_code == 200:
            dados_api = response.json().get('dados', [])
            print("Dados da API instrutores:", dados_api)  # <-- Debug

            instrutores = []

            for instrutor in dados_api:
                status = 'Ativo' if instrutor.get('ativo', False) else 'Inativo'
                instrutor['status'] = status
                instrutores.append(instrutor)
        else:
            instrutores = []
            error_message = response.json().get('message', 'Erro desconhecido')
            print(f"Erro ao buscar instrutores: {error_message}")
            messages.error(request, f"Erro ao buscar instrutores: {error_message}")

    except requests.exceptions.RequestException as e:
        instrutores = []
        print(f"Erro de conexão com a API: {str(e)}")
        messages.error(request, f"Erro de conexão com a API: {str(e)}")

    total_instrutores = len(instrutores)
    print(f"Total instrutores encontrados: {total_instrutores}")

    return render(request, 'aluno/dashboard.html', {
    'instrutores': instrutores,
    'total_instrutores': total_instrutores
})