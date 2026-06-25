from django.core.management.base import BaseCommand
from django.db import transaction
from openpyxl import load_workbook
import os
from decimal import Decimal, InvalidOperation
from apps.products.models import Part, Category, LocalEstoque, Estoque

class Command(BaseCommand):
    help = 'Importa dados de peças a partir de um arquivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('caminho_excel', type=str, help='Caminho do arquivo na raiz')
        parser.add_argument('--categoria', type=str, default='Geral', help='Nome da categoria')

    def handle(self, *args, **kwargs):
        caminho_excel = kwargs['caminho_excel']
        nome_cat = kwargs['categoria']

        if not os.path.exists(caminho_excel):
            self.stdout.write(self.style.ERROR(f"❌ Arquivo '{caminho_excel}' não encontrado."))
            return

        categoria_obj, _ = Category.objects.get_or_create(name=nome_cat)
        local_padrao, _ = LocalEstoque.objects.get_or_create(
            nome_local="Depósito Central",
            defaults={'prateleira': 'A1', 'box': '01'}
        )

        self.stdout.write(self.style.WARNING(f"📊 Processando planilha. Categoria: {nome_cat}"))
        wb = load_workbook(caminho_excel, data_only=True)
        aba = wb.active

        sucessos = 0
        erros = 0

        # Iteramos pelas linhas pulando o cabeçalho (min_row=2)
        for index, linha in enumerate(aba.iter_rows(min_row=2, values_only=True), start=2):
            # Validação básica
            if not linha or linha[1] is None:
                continue

            try:
                # Mapeamento direto das colunas conforme a imagem (A=0, B=1, C=2, D=3)
                sku_planilha = str(linha[0]).strip() if linha[0] is not None else ""
                nome_produto = str(linha[1]).strip()
                qtd_bruta = linha[2]
                valor_bruto = str(linha[3]).strip() if linha[3] is not None else "0"

                # 1. Processar Quantidade
                qtd_final = int(float(qtd_bruta)) if qtd_bruta is not None else 0

                # 2. Processar Preço (Corrigido para aceitar milhar e decimal corretamente)
                # Remove R$, remove todos os pontos (milhar), troca vírgula por ponto (decimal)
                # Isso funciona tanto para '773.472,00' quanto para '145,00'
                valor_limpo = valor_bruto.replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    preco_final = Decimal(valor_limpo)
                except InvalidOperation:
                    preco_final = Decimal("0.00")

                # 3. Lógica de Salvamento
                with transaction.atomic():
                    # Se temos SKU na coluna 0, usamos ele. Se não, usamos o nome.
                    if sku_planilha and sku_planilha != "None":
                        part, _ = Part.objects.update_or_create(
                            sku=sku_planilha,
                            defaults={'name': nome_produto, 'category': categoria_obj}
                        )
                    else:
                        # Fallback (caso raro de não ter SKU)
                        part, _ = Part.objects.update_or_create(
                            name=nome_produto,
                            defaults={
                                'category': categoria_obj,
                                'sku': f"GEN-{hash(nome_produto) & 0xffffffff}"
                            }
                        )

                    # Atualiza Estoque
                    Estoque.objects.update_or_create(
                        produto=part,
                        defaults={
                            'local': local_padrao,
                            'quantidade': qtd_final,
                            'preco': preco_final
                        }
                    )

                sucessos += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erro na linha {index}: {e}"))
                erros += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Concluído! Cadastrados: {sucessos} | Falhas: {erros}"))