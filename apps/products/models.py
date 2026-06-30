from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from PIL import Image
import io
from django.core.files.base import ContentFile
import os
import traceback

# 1. CATEGORIAS DE PEÇAS
class Category(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        
    def __str__(self):
        return self.name

# 2. TABELA DE VEÍCULOS
class Veiculo(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=100)
    versao = models.CharField(max_length=100, blank=True, null=True)
    ano = models.IntegerField()
    motor = models.CharField(max_length=50)
    chassi = models.CharField(max_length=17, unique=True, blank=True, null=True)
    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano})"

# 3. TABELA DE PRODUTOS
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
        # Lógica de SKU e OEM
        if self.sku:
            self.sku = self.sku.strip()
        if not self.codigo_oem or not self.codigo_oem.strip():
            self.codigo_oem = f"OEM-{self.sku}"
        else:
            self.codigo_oem = self.codigo_oem.strip()

        # Lógica de conversão para WebP
        if self.image and hasattr(self.image, 'file'):
            try:
                # Abre a imagem original
                img = Image.open(self.image)
                
                # Só processa se não for já WebP
                if img.format != 'WEBP':
                    output = io.BytesIO()
                    
                    # Converte para RGB (necessário para salvar PNGs com transparência como WebP)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                        
                    img.save(output, format='WEBP', quality=85)
                    output.seek(0)
                    
                    nome_base = os.path.splitext(self.image.name)[0]
                    # Salva o novo arquivo, mantendo a referência da imagem
                    self.image.save(f"{nome_base}.webp", ContentFile(output.read()), save=False)
            except Exception as e:
                # Imprime o erro no console do Render, mas deixa o fluxo prosseguir
                print(f"Erro ao converter imagem para WebP: {e}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.name}"

# 4. LOCAIS DE ESTOQUE
class LocalEstoque(models.Model):
    nome_local = models.CharField(max_length=100)
    prateleira = models.CharField(max_length=50)
    box = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.nome_local} - Prat: {self.prateleira} / Box: {self.box}"

# 5. ESTOQUE (Saldo)
class Estoque(models.Model):
    produto = models.OneToOneField(Part, on_delete=models.CASCADE, related_name='estoque')
    local = models.ForeignKey(LocalEstoque, on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=0)
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    def save(self, *args, **kwargs):
        if self.preco and self.preco >= 100000:
            self.preco = self.preco / 100

        if self.preco > 1000000:
            print("--- ALERTA: PREÇO AINDA ESTÁ MUITO ALTO APÓS NORMALIZAÇÃO ---")
            print(f"Produto/SKU: {self.produto.sku if self.produto else 'N/A'}")
            print(f"Valor final do Preço: {self.preco}") 
            traceback.print_stack()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produto.name} -> {self.quantidade} un"

# 6. MOVIMENTAÇÕES
class Movimentacao(models.Model):
    TIPO_CHOICES = [('E', 'Entrada'), ('S', 'Saída')]
    produto = models.ForeignKey(Part, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    data_hora = models.DateTimeField(auto_now_add=True)
    historico_usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    
    def __str__(self):
        tipo_display = getattr(self, 'get_tipo_display', lambda: self.tipo)()
        return f"{tipo_display} - {self.quantidade}x {self.produto.name}"

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