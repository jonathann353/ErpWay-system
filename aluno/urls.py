from django.urls import path
from . import views

urlpatterns = [
    # path('politica-privacidade/', views.Politica_Privacidade, name="politica_privacidade"),
    # path('termo-de-uso/', views.Termo_de_uso, name="termo_de_uso"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('Aluno/', views.Aluno, name='aluno'),
    # path('instrutor/', views.instrutor_view, name='instrutor'),
    # path('salvar-treino/', views.salvar_treino, name='salvar_treino'),
    path("login/", views.login_view, name='login'),
    path("register/", views.register_view, name="register"),
    path('logout/', views.logout_view, name='logout'),
    path('Aluno/editar/<int:cod_aluno>/', views.editar_aluno, name='editar_aluno'),
    path('buscar/', views.buscar_global, name='buscar_global'),
    path('filtrar/', views.filtrar_alunos, name='filtrar_alunos'),
    path('cadastrar-aluno/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('perfil/<int:cod_aluno>/', views.perfil, name='perfil'),
    path('treinos/peito/', views.treinos_peito, name='treinos_peito'),
    path('listar/instrutor/', views.listar_instrutores, name='listar_instrutores'),
]
