import uuid
import random
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse
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
    aluno = {}
    treinos = []

    try:
        # Buscar dados do aluno via API Flask
        response = requests.get(f'https://api-flask-academia.onrender.com/busca/aluno/{cod_aluno}')

        if response.status_code == 200:
            dados = response.json().get('dados', [])
            aluno = next((a for a in dados if str(a.get('cod_aluno')) == str(cod_aluno)), {})
        else:
            error_message = response.json().get('message', 'Erro desconhecido')
            messages.error(request, f"Erro ao buscar aluno: {error_message}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erro de conexão com a API: {str(e)}")

    try:
        # Buscar treinos diretamente no Supabase
        treino_result = supabase.table("treino").select("*").eq("cod_aluno", cod_aluno).execute()
        treinos = treino_result.data if treino_result.data else []
    except Exception as e:
        messages.error(request, f"Erro ao buscar treinos: {str(e)}")

    contexto = {
        'aluno': aluno,
        'treinos': treinos
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

        hashed_input_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        try:
            # Buscar usuário no Supabase
            response = supabase.table("auth_user").select("*").eq("username", username).execute()
            user_data = response.data

            if user_data:
                user = user_data[0]
                stored_password_hash = user['password']

                if hashed_input_password == stored_password_hash:
                    # Salvar dados na sessão
                    request.session['username'] = user['username']
                    request.session['user_id'] = user['id']

                    # Verifica se é superusuário
                    if user.get('is_superuser', False):
                        return redirect('dashboard')

                    # Verifica se é instrutor
                    instrutor_response = supabase.table("instrutor").select("cod_instrutor").eq("ID_auth", user['id']).execute()
                    instrutor_data = instrutor_response.data

                    if instrutor_data:
                        cod_instrutor = instrutor_data[0]['cod_instrutor']
                        return redirect('dashboard_instrutor', cod_instrutor=cod_instrutor)

                    # Verifica se é aluno
                    aluno_response = supabase.table("aluno").select("cod_aluno").eq("ID_auth", user['id']).execute()
                    aluno_data = aluno_response.data

                    if aluno_data:
                        cod_aluno = aluno_data[0]['cod_aluno']
                        return redirect('perfil', cod_aluno=cod_aluno)

                    messages.error(request, "Usuário autenticado, mas não vinculado como aluno ou instrutor.")
                    return redirect('login')

                else:
                    return render(request, 'accounts/login.html', {'error': 'Senha incorreta.'})
            else:
                return render(request, 'accounts/login.html', {'error': 'Usuário não encontrado.'})

        except Exception as e:
            return render(request, 'accounts/login.html', {'error': f'Erro no login: {str(e)}'})

    return render(request, 'accounts/login.html')

##################instrutor########################
# URL base da API Flask hospedada no Render
BASE_URL = 'https://api-flask-academia.onrender.com'

def dashboard_instrutor(request, cod_instrutor):
    try:
        url = f'{BASE_URL}/alunos/do/instrutor/{cod_instrutor}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        alunos = data.get('alunos', [])
        instrutor_id = data.get('instrutor_id')

        context = {
            'instrutor_id': instrutor_id,
            'alunos': alunos,
            'year': datetime.now().year
        }
        return render(request, 'instrutor/dashboard.html', context)

    except requests.exceptions.RequestException as e:
        return render(request, 'instrutor/dashboard.html', {
            'error': 'Erro ao se comunicar com a API.',
            'exception': str(e)
        })

    except Exception as e:
        return render(request, 'instrutor/dashboard.html', {
            'error': 'Erro inesperado ao carregar os dados.',
            'exception': str(e)
        })
        
@csrf_exempt
def adicionar_treino(request):
    if request.method == 'POST':
        try:
            cod_aluno = request.POST.get('cod_aluno')
            cod_instrutor = request.POST.get('cod_instrutor')

            if not cod_aluno or not cod_instrutor:
                return HttpResponseBadRequest("Código do aluno ou instrutor ausente.")

            cod_aluno = int(cod_aluno)
            cod_treino = random.randint(100000, 999999)
            request.session['cod_treino'] = cod_treino

            treino_payload = {
                "cod_treino": cod_treino,
                "tipo_treino": request.POST.get('tipo_treino'),
                "cod_aluno": cod_aluno,
                "cod_instrutor": cod_instrutor,
                "objetivo": request.POST.get('objetivo', ''),
                "observacoes": request.POST.get('observacoes', ''),
                "data_inicio": request.POST.get('data_inicio'),
                "data_final": request.POST.get('data_final') or None
            }

            treino_response = requests.post(f"{BASE_URL}/criar/treino/aluno", json=treino_payload)

            if treino_response.status_code not in [200, 201]:
                print("Erro ao criar treino:", treino_response.text)
                return HttpResponseBadRequest("Erro ao criar treino.")

            # Retorna o código do treino criado para ser usado na próxima requisição
            return JsonResponse({"cod_treino": cod_treino})

        except ValueError:
            return HttpResponseBadRequest("Código inválido.")
        except Exception as e:
            print("Erro inesperado:", e)
            return HttpResponseBadRequest("Erro interno.")

        
@csrf_exempt
def adicionar_exercicio(request):
    if request.method == 'POST':
        try:
            # Recupera o cod_treino salvo anteriormente
            cod_treino = request.session.get('cod_treino')

            if not cod_treino:
                return HttpResponseBadRequest("Código do treino ausente.")

            exercicio_payload = {
                "Cod_treino": cod_treino,
                "nome": request.POST.get('nome_exercicio'),
                "tipo_treino": request.POST.get('tipo_exercicio'),
                "discricao": request.POST.get('descricao_exercicio')  # ⚠️ com S, se a API exigir
            }

            exercicio_response = requests.post(f"{BASE_URL}/criar/exercicio/treino", json=exercicio_payload)

            if exercicio_response.status_code not in [200, 201]:
                print("Erro ao criar exercício:", exercicio_response.text)
                return HttpResponseBadRequest("Erro ao criar exercício.")

            return JsonResponse({"message": "Exercício criado com sucesso."})

        except Exception as e:
            print("Erro inesperado:", e)
            return HttpResponseBadRequest("Erro interno.")
        
###########

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