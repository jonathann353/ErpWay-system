from django.db import models
from django.contrib.auth.models import User

class Aula(models.Model):
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aulas')
    data_hora = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField(default=60)
    assunto = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('agendada', 'Agendada'), ('cancelada', 'Cancelada'), ('realizada', 'Realizada')],
        default='agendada'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Aula de {self.aluno.username} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
    
    
class ProdutoAdmin(models.Model):
    cod_treino = models.IntegerField(unique=True)  # novo campo para usar como identificador
    nome = models.CharField(max_length=100)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.nome