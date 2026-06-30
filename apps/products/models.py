from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import os

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name

class Veiculo(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=100)
    versao = models.CharField(max_length=100, blank=True, null=True)
    ano = models.IntegerField()
    motor = models.CharField(max_length=50)
    chassi = models.CharField(max_length=17, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano})"

class Part(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='parts')
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='produtos/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    peso = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.000'))
    dimensoes = models.CharField(max_length=100, default="Não Informado")
    codigo_oem = models.CharField(max_length=100, blank=True, null=True)
    is_generic = models.BooleanField(default=False)
    veiculos_compativeis = models.ManyToManyField(Veiculo, related_name="pecas_compativeis", blank=True)

    def save(self, *args, **kwargs):
        # Apenas lógica de normalização de texto
        if self.sku:
            self.sku = self.sku.strip()
        if not self.codigo_oem or not self.codigo_oem.strip():
            self.codigo_oem = f"OEM-{self.sku}"
        else:
            self.codigo_oem = self.codigo_oem.strip()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.name}"

class LocalEstoque(models.Model):
    nome_local = models.CharField(max_length=100)
    prateleira = models.CharField(max_length=50)
    box = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nome_local} - Prat: {self.prateleira} / Box: {self.box}"

class Estoque(models.Model):
    produto = models.OneToOneField(Part, on_delete=models.CASCADE, related_name='estoque')
    local = models.ForeignKey(LocalEstoque, on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=0)
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    def save(self, *args, **kwargs):
        if self.preco and self.preco >= 100000:
            self.preco = self.preco / 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produto.name} -> {self.quantidade} un"

class Movimentacao(models.Model):
    TIPO_CHOICES = [('E', 'Entrada'), ('S', 'Saída')]
    produto = models.ForeignKey(Part, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    data_hora = models.DateTimeField(auto_now_add=True)
    historico_usuario = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.quantidade}x {self.produto.name}"

class RevisaoDados(models.Model):
    nome_produto = models.CharField(max_length=255)
    sku_tentativa = models.CharField(max_length=100, blank=True, null=True)
    preco_tentativa = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=255)
    data_criacao = models.DateTimeField(auto_now_add=True)
    resolvido = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Revisão de Dados"
        verbose_name_plural = "Revisões de Dados"

    def __str__(self):
        return f"{self.nome_produto} - {self.motivo}"