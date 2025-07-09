from django.urls import path
from . import views

urlpatterns = [
    # path('politica-privacidade/', views.Politica_Privacidade, name="politica_privacidade"),
    # path('termo-de-uso/', views.Termo_de_uso, name="termo_de_uso"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('Aluno/', views.Aluno, name='aluno'),
    # path('instrutor/', views.instrutor_view, name='instrutor'),
    # path('salvar-treino/', views.salvar_treino, name='salvar_treino'),
    path("", views.login_view, name='login'),
    path("register/", views.register_view, name="register"),
    path('logout/', views.logout_view, name='logout'),
    path('Aluno/editar/<int:cod_aluno>/', views.editar_aluno, name='editar_aluno'),
    path('buscar/', views.buscar_global, name='buscar_global'),
    path('filtrar/', views.filtrar_alunos, name='filtrar_alunos'),
    path('cadastrar-aluno/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('perfil/<int:cod_aluno>/', views.perfil, name='perfil'),
    path('listar/instrutor/', views.listar_instrutores, name='listar_instrutores'),
    path('instrutor/dashboard/', views.dashboard_instrutor, name='dashboard_instrutor'),
    path('dashboard_instrutor/<int:cod_instrutor>/', views.dashboard_instrutor, name='dashboard_instrutor'),
    path('adicionar-treino/', views.adicionar_treino, name='adicionar_treino'),
    path("api/treinos/aluno/<int:cod_aluno>/", views.listar_treinos_do_aluno, name="listar_treinos_do_aluno"),
    path("adicionar-exercicios/", views.adicionar_exercicios_ao_treino, name="adicionar_exercicios_ao_treino"),
    path('avaliacao/do/instrutor/<int:cod_instrutor>/', views.salvar_avaliacao, name='salvar_avaliacao'),
    path('avaliacoes/<int:cod_aluno>/', views.listar_avaliacoes, name='listar_avaliacoes'),
    path('atualizar/exercicio/<int:cod_aluno>/<int:cod_exercicio>/', views.atualizar_status, name='atualizar_status'),
    path('pagamento/<int:cod_aluno>/', views.criar_pagamento_pix, name='criar_pagamento_pix'),
    path('webhook/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('dashboard/pagamentos/<int:cod_aluno>/', views.listar_pagamentos, name='listar_pagamentos'),
    path('pagamento/atualizar/<str:payment_id>/', views.atualizar_status_pagamento, name='atualizar_status_pagamento'),
    
]
