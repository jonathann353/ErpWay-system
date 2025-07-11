import uuid
import random
import logging
import mercadopago
import json
import base64
import io
import matplotlib.pyplot as plt
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from dateutil import parser
from django.conf import settings
from datetime import datetime
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
import requests
from types import SimpleNamespace
import hashlib
from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from supabase import create_client, Client
from .decorators import login_required_custom
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime


sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
url = "https://pgdldfqzqgxowqedrldh.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnZGxkZnF6cWd4b3dxZWRybGRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc1Nzk0MjksImV4cCI6MjA1MzE1NTQyOX0.jntDjoG90UW916FljiMlrmM4YqaNLeTphwTO2IPkY9E"
supabase: Client = create_client(url, key)


logger = logging.getLogger(__name__)

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
    avaliacoes = []
    ultima_avaliacao = None
    mapa_instrutores = {}
    dia = datetime.now()
    data_formatada = dia.strftime('%d/%m/%Y')
    ano = datetime.now().year

    # 🔍 Buscar dados do aluno
    try:
        url_aluno = f'https://api-flask-academia.onrender.com/busca/aluno/{cod_aluno}'
        response = requests.get(url_aluno)

        if response.status_code == 200:
            dados = response.json()
            dados_aluno = dados.get('dados', [])
            aluno = dados_aluno[0] if dados_aluno else {}
        else:
            messages.error(request, "Erro ao buscar dados do aluno.")
    except Exception as e:
        messages.error(request, f"Erro na API de aluno: {str(e)}")

    # 🔍 Buscar dados dos instrutores
    try:
        url_instrutor = 'https://api-flask-academia.onrender.com/listar/instrutor'
        response = requests.get(url_instrutor)

        if response.status_code == 200:
            dados_instrutores_raw = response.json()
            dados_instrutores = dados_instrutores_raw.get('dados', [])

            mapa_instrutores = {
                int(instrutor.get('cod_instrutor')): instrutor.get('nome')
                for instrutor in dados_instrutores if isinstance(instrutor, dict)
            }

            print("Instrutores formatados:", mapa_instrutores)

        else:
            messages.error(request, "Erro ao buscar dados dos instrutores.")
    except Exception as e:
        messages.error(request, f"Erro na API de instrutores: {str(e)}")

    cod_instrutor = None  # Define fora do if para evitar UnboundLocalError

    if aluno:
        aluno['status'] = 'Ativo' if aluno.get('status') else 'Inativo'

        # Captura e força o tipo inteiro
        cod_instrutor_raw = aluno.get('Cod_instrutor') or aluno.get('cod_instrutor')
        try:
            cod_instrutor = int(cod_instrutor_raw) if cod_instrutor_raw else None
        except (ValueError, TypeError):
            cod_instrutor = None

        # Usa mapa_instrutores com int nas chaves
        aluno['nome_instrutor'] = mapa_instrutores.get(cod_instrutor, 'Não atribuído')
        print("dados_instrutores:", dados_instrutores)
        print("tipo dos itens:", [type(instrutor) for instrutor in dados_instrutores])
        dados_instrutores_raw = response.json()
        dados_instrutores = dados_instrutores_raw.get('dados', [])

        mapa_instrutores = {
            int(instrutor.get('cod_instrutor')): instrutor.get('nome')
            for instrutor in dados_instrutores if isinstance(instrutor, dict) and instrutor.get('cod_instrutor') is not None
        }

    # 🔍 Buscar treinos e exercícios
        try:
            url_treinos = f'https://api-flask-academia.onrender.com/detalhes/treino/aluno/{cod_aluno}'
            response = requests.get(url_treinos)

            if response.status_code == 200:
                dados_treinos = response.json()

                if isinstance(dados_treinos, list):
                    for item in dados_treinos:
                        treino_data = item.get('treino', {})

                        # Conversão segura das datas
                        data_inicio = treino_data.get('data_inicio')
                        data_final = treino_data.get('data_final')

                        try:
                            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date() if data_inicio else None
                        except Exception:
                            data_inicio = None

                        try:
                            data_final = datetime.strptime(data_final, '%Y-%m-%d').date() if data_final else None
                        except Exception:
                            data_final = None

                        treino = {
                            'cod_treino': treino_data.get('cod_treino'),
                            'tipo_treino': treino_data.get('tipo_treino'),
                            'objetivo': treino_data.get('objetivo'),
                            'observacoes': treino_data.get('observacoes'),
                            'data_inicio': data_inicio,
                            'data_final': data_final,
                            'exercicios': []
                        }

                        exercicios = treino_data.get('exercicios', [])
                        for ex in exercicios:
                            treino['exercicios'].append({
                                'cod_exercicio': ex.get('cod_exercicio'),
                                'nome_exercicio': ex.get('nome_exercicio'),
                                'serie': ex.get('serie'),
                                'repeticoes': ex.get('repeticoes'),
                                'carga': ex.get('carga'),
                                'observacao': ex.get('observacao'),
                                'concluido': ex.get('concluido', False)
                            })

                        treinos.append(treino)
            else:
                messages.error(request, "Erro ao buscar dados dos treinos.")
        except Exception as e:
            messages.error(request, f"Erro na API de treinos: {str(e)}")

    # 🔍 Buscar avaliações
    try:
        url = f'https://api-flask-academia.onrender.com/avaliacoes/do/aluno/{cod_aluno}'
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            dados = response.json()
            lista_avaliacoes = dados.get('avaliacoes', [])

            for item in lista_avaliacoes:
                avaliacao = SimpleNamespace(**item)
                if hasattr(avaliacao, 'data_avaliacao') and isinstance(avaliacao.data_avaliacao, str):
                    try:
                        avaliacao.data_avaliacao = datetime.strptime(avaliacao.data_avaliacao, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                avaliacoes.append(avaliacao)

            avaliacoes = sorted(avaliacoes, key=lambda x: x.data_avaliacao, reverse=True)
            ultima_avaliacao = avaliacoes[0] if avaliacoes else None
        else:
            messages.error(request, "Erro ao buscar avaliações.")
    except Exception as e:
        messages.error(request, f"Erro na API de avaliações: {str(e)}")

    # 🔥 Buscar pagamentos no Supabase
    try:
        pagamentos_resp = supabase.table('pagamentos').select("*").eq("aluno", cod_aluno).order("criado_em", desc=True).execute()
        pagamentos = pagamentos_resp.data or []

        for pag in pagamentos:
            if 'criado_em' in pag and pag['criado_em']:
                pag['criado_em'] = parser.parse(pag['criado_em'])
    except Exception as e:
        messages.error(request, f"Erro ao buscar pagamentos: {str(e)}")
        pagamentos = []

    # 🔍 Pega o último pagamento (se tiver)
    ultimo_pagamento = pagamentos[0] if pagamentos else None

    # 🔥 Calcular progresso (peso e IMC)
    peso_diferenca = None
    peso_percentual = None
    imc_diferenca = None
    imc_percentual = None

    if len(avaliacoes) >= 2:
        atual = avaliacoes[0]
        anterior = avaliacoes[1]

        try:
            peso_diferenca = round(atual.peso - anterior.peso, 2)
            peso_percentual = round((peso_diferenca / anterior.peso) * 100, 2)

            imc_diferenca = round(atual.imc - anterior.imc, 2)
            imc_percentual = round((imc_diferenca / anterior.imc) * 100, 2)

        except (TypeError, ZeroDivisionError):
            peso_diferenca = None
            peso_percentual = None
            imc_diferenca = None
            imc_percentual = None

    # Extrair dados para gráfico
    meta = ultima_avaliacao.meta if ultima_avaliacao else None
    labels = [a.data_avaliacao.strftime('%d/%m') for a in avaliacoes if a.data_avaliacao]
    pesos = [a.peso for a in avaliacoes]
    imcs = [a.imc for a in avaliacoes]
    
    # 🔥 Contador decrescente do treino (dias restantes)
    dias_restantes_treino = None

    try:
        treino_ativo = None
        hoje = datetime.now().date()

        for treino in treinos:
            data_final = treino.get('data_final')
            if data_final:
                try:
                    data_final_convertida = datetime.strptime(data_final, '%Y-%m-%d').date()
                    if data_final_convertida >= hoje:
                        treino_ativo = treino
                        break
                except Exception:
                    continue

        if treino_ativo:
            data_final = datetime.strptime(treino_ativo.get('data_final'), '%Y-%m-%d').date()
            dias_restantes_treino = (data_final - hoje).days

    except Exception as e:
        dias_restantes_treino = None

    # 🔥 Contexto final
    contexto = {
        'cod_aluno': cod_aluno,
        'treinos': treinos,
        'aluno': aluno,
        'data_formatada': data_formatada,
        'ano': ano,
        'avaliacoes': avaliacoes,
        'ultima_avaliacao': ultima_avaliacao,
        'peso_diferenca': peso_diferenca,
        'peso_percentual': peso_percentual,
        'imc_diferenca': imc_diferenca,
        'imc_percentual': imc_percentual,
        'grafico_labels': labels,
        'grafico_pesos': pesos,
        'grafico_imcs': imcs,
        'meta_peso': meta,

        # 🔥 Pagamentos
        'pagamentos': pagamentos,
        'qr_code': ultimo_pagamento.get('qr_code') if ultimo_pagamento else None,
        'qr_code_base64': ultimo_pagamento.get('qr_code_base64') if ultimo_pagamento else None,
        'status': ultimo_pagamento.get('status') if ultimo_pagamento else None,
        'valor': ultimo_pagamento.get('valor') if ultimo_pagamento else None,

        # 🔥 Dias restantes do treino
        'dias_restantes_treino': dias_restantes_treino,
    }

    return render(request, 'aluno/perfil.html', contexto)

@csrf_exempt
def listar_treinos_do_aluno(request, cod_aluno):
    if request.method != "GET":
        return JsonResponse({"message": "Método não permitido."}, status=405)

    try:
        url = f"{BASE_URL}/detalhes/treino/aluno/{cod_aluno}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return JsonResponse(data, safe=False)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"message": "Erro ao consultar treinos.", "erro": str(e)}, status=400)

    
def atualizar_status(request, cod_exercicio, cod_aluno):
    if request.method == 'POST':
        status = request.POST.get('status') == 'on'  # Checkbox retorna 'on' se estiver marcado

        dados = {
            'concluido': status
        }

        url_api = f"https://api-flask-academia.onrender.com/atualizar/exercicio/{cod_exercicio}"

        try:
            response = requests.put(url_api, json=dados, timeout=5)

            if response.status_code == 200:
                messages.success(request, 'Status do exercício atualizado com sucesso!')
            else:
                erro = response.json().get('message', 'Erro desconhecido')
                messages.error(request, f"Erro da API: {erro}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erro ao conectar com API: {e}")

        return redirect('perfil', cod_aluno=cod_aluno)

    return render(request, 'aluno/perfil.html', {'cod_exercicio': cod_exercicio, 'cod_aluno': cod_aluno})


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
            'Cod_plano': request.POST.get('plano')
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

def graficos(request):
    url = 'https://api-flask-academia.onrender.com/listar/aluno'

    try:
        response = requests.get(url)
        response.raise_for_status()
        alunos = response.json()

        ativos = sum(1 for aluno in alunos if aluno.get('status') == True)
        inativos = sum(1 for aluno in alunos if aluno.get('status') == False)

        labels = ['Ativos', 'Inativos']
        data = [ativos, inativos]

    except Exception as e:
        print(f"Erro na API: {e}")
        labels = ['Ativos', 'Inativos']
        data = [0, 0]

    return render(request, 'aluno/dashboard.html', {
        'labels': labels,
        'data': data
    })  

@login_required_custom
def dashboard(request):
    alunos = []
    mapa_instrutores = {}

    # --- Consulta de alunos ---
    try:
        response = requests.get('https://api-flask-academia.onrender.com/listar/aluno')

        if response.status_code == 200:
            dados_api = response.json().get('dados', [])
        else:
            dados_api = []
            error_message = response.json().get('message', 'Erro desconhecido')
            messages.error(request, f"Erro ao buscar alunos: {error_message}")

    except requests.exceptions.RequestException as e:
        dados_api = []
        messages.error(request, f"Erro de conexão com a API: {str(e)}")

    # --- Consulta de instrutores ---
    instrutores = []
    try:
        response_instrutor = requests.get('https://api-flask-academia.onrender.com/listar/instrutor')

        if response_instrutor.status_code == 200:
            dados_instrutor = response_instrutor.json().get('dados', [])
            instrutores = dados_instrutor

            mapa_instrutores = {
                instrutor['cod_instrutor']: instrutor['nome']
                for instrutor in instrutores
            }

        else:
            error_message = response_instrutor.json().get('message', 'Erro desconhecido')
            messages.error(request, f"Erro ao buscar instrutores: {error_message}")

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erro de conexão com a API (instrutores): {str(e)}")

    # --- Processa os alunos ---
    total_inativos = 0  # Variável para contar inativos

    for aluno in dados_api:
        status = 'Ativo' if aluno.get('status') else 'Inativo'
        aluno['status'] = status

        if status == 'Inativo':
            total_inativos += 1  # Incrementa se for inativo

        cod_instrutor = aluno.get('Cod_instrutor')
        aluno['nome_instrutor'] = mapa_instrutores.get(cod_instrutor, 'Não atribuído')

        alunos.append(aluno)

    total_alunos = len(alunos)
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
    
    planos = consultar_planos_supabase()
    return render(request, 'aluno/dashboard.html', {
        'alunos': alunos,
        'total_alunos': total_alunos,
        'total_instrutores': total_instrutores,
        'total_inativos': total_inativos,  # Envia para o template
        'instrutores': instrutores,
        'soma_valores': soma_valores,
        'ultimo_pagamento': ultimo_valor_pago,
        'planos': planos,
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

def obter_nome_instrutor(data):
    """Extrai o nome do instrutor, tentando vários formatos conhecidos."""
    try:
        nome = (
            (data.get('instrutor') or {}).get('nome') or
            (data.get('instrutor') or {}).get('nome_instrutor') or
            data.get('instrutor_nome') or
            data.get('nome_instrutor')
        )
        if not nome:
            logger.warning(f'Nome do instrutor não encontrado nos dados: {data}')
            return 'Nome não disponível'
        return nome
    except Exception as e:
        logger.error(f'Erro ao obter nome do instrutor: {e}')
        return 'Nome não disponível'


def dashboard_instrutor(request, cod_instrutor):
    dia = datetime.today().strftime('%d/%m/%Y')

    # Primeiro busca os dados dos alunos do instrutor
    try:
        url = f'{BASE_URL}/alunos/do/instrutor/{cod_instrutor}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        print(f"DEBUG dashboard instrutor cod_instrutor={cod_instrutor}: {data}")

        alunos = data.get('alunos', [])

        for aluno in alunos:
            cod_aluno = aluno.get('cod_aluno')

            # Tenta usar o status da API primeiro
            status_api = aluno.get('status')

            if status_api in ['Ativo', 'Inativo']:
                aluno['status'] = status_api
            else:
                try:
                    result = supabase.table('pagamentos') \
                        .select('status') \
                        .eq('aluno', cod_aluno) \
                        .order('criado_em', desc=True) \
                        .limit(1) \
                        .execute()

                    pagamentos = result.data or []
                    status_pagamento = pagamentos[0]['status'] if pagamentos else None
                    aluno['status'] = 'Ativo' if status_pagamento == 'aprovado' else 'Inativo'

                except Exception as e:
                    print(f"Erro ao buscar status do aluno {cod_aluno}: {e}")
                    aluno['status'] = 'Inativo'


        instrutor_id = data.get('instrutor_id') or cod_instrutor
        mapa_alunos = {aluno['cod_aluno']: aluno['nome'] for aluno in alunos}
        alunos_ids = list(mapa_alunos.keys())

    except requests.exceptions.RequestException as e:
        return render(request, 'instrutor/dashboard.html', {
            'error': 'Erro ao se comunicar com a API.',
            'exception': str(e)
        })

    # Busca a lista de instrutores para obter o nome
    try:
        url_instrutor = 'https://api-flask-academia.onrender.com/listar/instrutor'
        resp_instrutor = requests.get(url_instrutor)
        resp_instrutor.raise_for_status()

        dados_instrutor = resp_instrutor.json().get('dados', [])
        mapa_instrutores = {
            instrutor.get('cod_instrutor'): instrutor.get('nome')
            for instrutor in dados_instrutor
        }

        instrutor_nome = mapa_instrutores.get(instrutor_id, 'Nome não disponível')

    except requests.exceptions.RequestException as e:
        instrutor_nome = 'Nome não disponível'
        print(f"Erro ao buscar instrutor: {e}")
    
    # Últimos 5 treinos do instrutor
    try:
        treinos_resp = supabase \
            .table('treino') \
            .select('cod_treino, tipo_treino, data_inicio, cod_aluno') \
            .eq('cod_instrutor', cod_instrutor) \
            .order('data_inicio', desc=True) \
            .limit(5) \
            .execute()
        ultimos_treinos = treinos_resp.data or []
    except Exception as e:
        print(f"Erro ao buscar treinos: {e}")
        ultimos_treinos = []

    # Últimas 5 avaliações físicas do instrutor
    try:
        aval_resp = supabase \
            .table('avaliacao_fisica') \
            .select('id, data_avaliacao, cod_aluno') \
            .eq('cod_instrutor', cod_instrutor) \
            .order('data_avaliacao', desc=True) \
            .limit(5) \
            .execute()
        ultimas_avaliacoes = aval_resp.data or []
    except Exception as e:
        print(f"Erro ao buscar avaliações: {e}")
        ultimas_avaliacoes = []

    # ➕ Contador de treinos do instrutor
    try:
        treino_resp = supabase.table('treino').select('cod_treino', count='exact').eq('cod_instrutor', cod_instrutor).execute()
        treino_count = treino_resp.count or 0
    except Exception as e:
        print(f"Erro ao contar treinos: {e}")
        treino_count = 0

    # ➕ Contador de avaliações físicas feitas pelo instrutor
    try:
        aval_resp = supabase.table('avaliacao_fisica').select('id', count='exact').eq('cod_instrutor', cod_instrutor).execute()
        avaliacao_count = aval_resp.count or 0
    except Exception as e:
        print(f"Erro ao contar avaliações: {e}")
        avaliacao_count = 0

    context = {
        'cod_instrutor': cod_instrutor,
        'instrutor_nome': instrutor_nome,
        'alunos': alunos,
        'dia': dia,
        'year': datetime.now().year,
        'treino_count': treino_count,
        'avaliacao_count': avaliacao_count,
        'ultimos_treinos': ultimos_treinos,
        'ultimas_avaliacoes': ultimas_avaliacoes,
        'mapa_alunos': mapa_alunos,
        'alunos_ids': alunos_ids,
    }

    return render(request, 'instrutor/dashboard.html', context)



@csrf_exempt
def salvar_avaliacao(request, cod_instrutor):
    if request.method == 'POST':
        try:
            cod_aluno = request.POST.get('cod_aluno')
            data_avaliacao = request.POST.get('data_avaliacao')
            peso = request.POST.get('peso')
            altura = request.POST.get('altura')
            imc = request.POST.get('imc')
            meta = request.POST.get('meta')
            observacoes = request.POST.get('observacoes', '')

            if not (cod_aluno and data_avaliacao and peso and altura and imc):
                messages.error(request, 'Preencha todos os campos obrigatórios.')
                return redirect('dashboard_instrutor', cod_instrutor=cod_instrutor)

            avaliacao = {
                "cod_aluno": int(cod_aluno),
                "data_avaliacao": data_avaliacao,
                "peso": float(peso),
                "altura": float(altura),
                "imc": float(imc),
                "meta": float(meta), 
                "observacoes": observacoes
            }

            url = f"https://api-flask-academia.onrender.com/avaliacao/do/instrutor/{cod_instrutor}"
            response = requests.post(url, json=avaliacao)

            if response.status_code == 201:
                messages.success(request, 'Avaliação salva com sucesso!')
            else:
                erro_msg = response.json().get('message', 'Erro desconhecido ao salvar avaliação.')
                messages.error(request, f'Erro ao salvar avaliação: {erro_msg}')
        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')

        return redirect('dashboard_instrutor', cod_instrutor=cod_instrutor)

    messages.error(request, 'Método não permitido.')
    return redirect('dashboard_instrutor', cod_instrutor=cod_instrutor)

def listar_avaliacoes(request, cod_aluno):
    try:
        url = f'https://api-flask-academia.onrender.com/avaliacoes/do/aluno/{cod_aluno}'
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            dados = response.json()
            lista_avaliacoes = dados.get('avaliacoes', [])

            if isinstance(lista_avaliacoes, list):
                avaliacoes = []

                for item in lista_avaliacoes:
                    avaliacao = SimpleNamespace(**item)
                    if hasattr(avaliacao, 'data_avaliacao') and isinstance(avaliacao.data_avaliacao, str):
                        try:
                            avaliacao.data_avaliacao = datetime.strptime(avaliacao.data_avaliacao, '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    avaliacoes.append(avaliacao)

                avaliacoes = sorted(
                    avaliacoes,
                    key=lambda x: x.data_avaliacao,
                    reverse=True
                )

                # 🔥 Salvar na sessão para usar na view perfil
                request.session['avaliacoes'] = [
                    {
                        'data_avaliacao': str(av.data_avaliacao),
                        'peso': av.peso,
                        'altura': av.altura,
                        'imc': av.imc,
                        'cod_instrutor': av.cod_instrutor,
                        'cod_aluno': av.cod_aluno,
                        'observacoes': getattr(av, 'observacoes', '')
                    }
                    for av in avaliacoes
                ]

                request.session['ultima_avaliacao'] = request.session['avaliacoes'][0] if avaliacoes else None

        else:
            messages.error(request, "Erro ao buscar avaliações.")
    except Exception:
        messages.error(request, "Erro de conexão com a API de avaliações.")

    # ✅ Corrigido — envia apenas o código do aluno
    return redirect('perfil', cod_aluno=cod_aluno)

@csrf_exempt
def adicionar_treino(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Método não permitido."}, status=405)

    try:
        data = json.loads(request.body)

        cod_aluno = data.get('cod_aluno')
        cod_instrutor = data.get('cod_instrutor')
        tipo_treino = data.get('tipo_treino')
        data_inicio = data.get('data_inicio')
        dia_semana = data.get('dia_semana')

        if not all([cod_aluno, cod_instrutor, tipo_treino, data_inicio, dia_semana]):
            return JsonResponse({"message": "Todos os campos obrigatórios devem ser preenchidos."}, status=400)

        cod_treino = data.get('cod_treino') or int(uuid.uuid4().int % 1000000)  # número simples único

        treino_payload = {
            "cod_treino": cod_treino,
            "tipo_treino": tipo_treino,
            "cod_aluno": int(cod_aluno),
            "cod_instrutor": int(cod_instrutor),
            "objetivo": data.get('objetivo', ''),
            "observacoes": data.get('observacoes', ''),
            "data_inicio": data_inicio,
            "data_final": data.get('data_final') or None,
            "dia_semana": dia_semana
        }

        response = requests.post(f"{BASE_URL}/criar/treino/aluno", json=treino_payload)

        # 🔍 DEBUG: veja o que a API retorna
        print("=== RESPOSTA DA API ===")
        print("Status code:", response.status_code)
        print("Response text:", response.text)
        print("=======================")

        if response.status_code not in [200, 201]:
            return JsonResponse({
                "message": "Erro ao criar treino.",
                "erro": response.text,
                "payload": treino_payload
            }, status=400)

        return JsonResponse({
            "status": "success",
            "cod_treino": cod_treino,
            "api_response": response.json()  # mostra a resposta retornada pela API
        })

    except json.JSONDecodeError:
        return JsonResponse({"message": "Dados inválidos no corpo da requisição."}, status=400)
    except Exception as e:
        return JsonResponse({"message": f"Erro inesperado: {str(e)}"}, status=500)
@csrf_exempt
def adicionar_exercicios_ao_treino(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Método não permitido."}, status=405)

    try:
        data = json.loads(request.body)
        exercicios = data.get('exercicios', [])

        if not exercicios or not isinstance(exercicios, list):
            return JsonResponse({"message": "A lista de exercícios é obrigatória."}, status=400)

        for ex in exercicios:
            campos_obrigatorios = ['cod_treino', 'exercicio', 'serie', 'repeticao', 'intervalo']
            for campo in campos_obrigatorios:
                if campo not in ex:
                    return JsonResponse({"message": f"O campo {campo} é obrigatório."}, status=400)

            payload = {
                "cod_treino": ex["cod_treino"],
                "exercicio": ex["exercicio"],
                "serie": int(ex["serie"]),
                "repeticao": int(ex["repeticao"]),
                "intervalo": ex["intervalo"]
            }

            response = requests.post(f"{BASE_URL}/criar/exercicio/treino", json=payload)
            print(">>> ENVIANDO:", payload)
            print(">>> RESPOSTA:", response.status_code, response.text)

            if response.status_code not in [200, 201]:
                return JsonResponse({
                    "message": "Erro ao criar exercício na API Flask.",
                    "erro": response.text
                }, status=400)

        return JsonResponse({"status": "success", "message": "Exercícios cadastrados com sucesso."})

    except json.JSONDecodeError as e:
        return JsonResponse({"message": "Erro ao processar JSON.", "erro": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"message": f"Erro inesperado: {str(e)}"}, status=500)

def gerar_relatorio_pdf(request, cod_aluno):
    try:
        cod_instrutor = request.GET.get("cod_instrutor")
        if not cod_instrutor:
            return HttpResponse("Código do instrutor é obrigatório.", status=400)

        # Buscar todos os alunos do instrutor
        resp = requests.get(f"{BASE_URL}/alunos/do/instrutor/{cod_instrutor}")
        resp.raise_for_status()
        alunos = resp.json().get("alunos", [])
        aluno_data = next((a for a in alunos if a["cod_aluno"] == cod_aluno), None)
        if not aluno_data:
            return HttpResponse("Aluno não encontrado", status=404)

        # Treinos
        treinos_resp = supabase.table("treino").select("*").eq("cod_aluno", cod_aluno).execute()
        treinos = treinos_resp.data or []

        for treino in treinos:
            exercicios_resp = supabase.table("exercicio").select("*").eq("cod_treino", treino["cod_treino"]).execute()
            treino["exercicios"] = exercicios_resp.data or []

        # Avaliações físicas
        avaliacoes_resp = supabase.table("avaliacao_fisica").select("*").eq("cod_aluno", cod_aluno).execute()
        avaliacoes = avaliacoes_resp.data or []

        # Criar gráfico em memória (base64)
        grafico_imc = None
        if avaliacoes:
            datas = [datetime.strptime(a["data_avaliacao"], "%Y-%m-%d").strftime("%b/%Y") for a in avaliacoes if a.get("imc")]
            imcs = [a["imc"] for a in avaliacoes if a.get("imc")]
            if datas and imcs:
                plt.figure(figsize=(6, 3))
                plt.plot(datas, imcs, marker='o', linestyle='-', color='blue')
                plt.title("Evolução do IMC")
                plt.xlabel("Data")
                plt.ylabel("IMC")
                plt.grid(True)
                plt.tight_layout()

                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                plt.close()
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                grafico_imc = f"data:image/png;base64,{img_base64}"

        # Renderiza HTML
        html_string = render_to_string("instrutor/relatorio_pdf.html", {
            "aluno": aluno_data,
            "treinos": treinos,
            "avaliacoes": avaliacoes,
            "grafico_imc": grafico_imc,
        })

        # Gera PDF com WeasyPrint (tudo em memória)
        pdf_file = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="relatorio_aluno_{cod_aluno}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Erro: {e}", status=500)
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
    
def criar_pagamento_pix(request, cod_aluno):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        documento_tipo = request.POST.get('identificationType')
        documento_numero = request.POST.get('identificationNumber')
        valor = float(request.POST.get('valor'))

        pagamento_data = {
    "transaction_amount": valor,
    "description": "Mensalidade Academia",
    "payment_method_id": "pix",
    "payer": {
        "email": email,
        "first_name": nome,
        "last_name": "",
        "identification": {
            "type": documento_tipo,
            "number": documento_numero.replace('.', '').replace('-', '').replace('/', '')
        }
    },
        #     "back_urls": {
        #     "success": request.build_absolute_uri(reverse('pagamento_sucesso')),
        #     "pending": request.build_absolute_uri(reverse('pagamento_pendente')),
        #     "failure": request.build_absolute_uri(reverse('pagamento_falha')),
        # },
        # "auto_return": "approved"
        }

        pagamento_response = sdk.payment().create(pagamento_data)
        pagamento = pagamento_response["response"]

        if pagamento.get('id'):
            qr_code = pagamento["point_of_interaction"]["transaction_data"]["qr_code"]
            qr_code_base64 = pagamento["point_of_interaction"]["transaction_data"]["qr_code_base64"]
            status = pagamento["status"]
            mp_payment_id = str(pagamento["id"])

            # Salva no Supabase
            supabase.table('pagamentos').insert({
                "aluno": cod_aluno,
                "email": email,
                "valor": valor,
                "status": status,
                "mp_payment_id": mp_payment_id,
                "qr_code": qr_code,
                "qr_code_base64": qr_code_base64,
            }).execute()

            # 🔥 Exibe o QRCode diretamente
            return render(request, 'pagamento_qrcode.html', {
                'qr_code': qr_code,
                'qr_code_base64': qr_code_base64,
                'status': status,
                'valor': valor,
                'cod_aluno': cod_aluno
            })

        return JsonResponse({'error': 'Erro ao criar pagamento.'}, status=400)

    return redirect('perfil', cod_aluno=cod_aluno)

@csrf_exempt
def webhook_mercadopago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = str(data.get('data', {}).get('id'))

            if not payment_id:
                return JsonResponse({"error": "ID do pagamento ausente"}, status=400)

            pagamento = sdk.payment().get(payment_id)
            status = pagamento["response"].get("status")

            if status:
                supabase.table('pagamentos').update({"status": status}).eq("mp_payment_id", payment_id).execute()
                return JsonResponse({"status": "updated"})
            else:
                return JsonResponse({"error": "Status não encontrado"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Only POST allowed"}, status=400)


def listar_pagamentos(request, cod_aluno):
    pagamentos_resp = supabase.table('pagamentos').select("*").eq("aluno", cod_aluno).execute()
    pagamentos = pagamentos_resp.data or []

    # Converter strings de criado_em para datetime
    for pag in pagamentos:
        if 'criado_em' in pag and pag['criado_em']:
            pag['criado_em'] = parser.parse(pag['criado_em'])

    aluno_resp = supabase.table('aluno').select("*").eq('cod_aluno', cod_aluno).single().execute()
    aluno = aluno_resp.data

    return render(request, 'dashboard_pagamentos.html', {
        'pagamentos': pagamentos,
        'aluno': aluno,
        'cod_aluno': cod_aluno
    })
    
def atualizar_status_pagamento(request, payment_id):
    try:
        pagamento = sdk.payment().get(payment_id)
        status = pagamento["response"]["status"]

        supabase.table('pagamentos').update({"status": status}).eq("mp_payment_id", payment_id).execute()

        # ✅ Redireciona para o perfil do aluno depois de atualizar
        cod_aluno = request.GET.get('cod_aluno')
        return redirect('perfil', cod_aluno=cod_aluno)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
   
def consultar_planos_supabase():
    url = "https://pgdldfqzqgxowqedrldh.supabase.co/rest/v1/planos"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            planos = response.json()
            print("✔ Planos retornados do Supabase:")
            for plano in planos:
                print(f"- ID: {plano.get('id')} | Nome: {plano.get('nome')} | Valor: R$ {plano.get('valor_mensal')}")
            return planos
        else:
            print(f"❌ Erro ao buscar planos: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erro de conexão com Supabase: {str(e)}")
        return []

