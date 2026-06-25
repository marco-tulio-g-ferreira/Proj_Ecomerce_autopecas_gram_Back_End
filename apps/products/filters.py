# apps/products/filters.py
from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Part
from .constants import MARCAS_SINONIMOS

class PartFilter(filters.FilterSet):
    # Intercepta o filtro de marca para aplicar a lógica customizada de sinônimos
    veiculos_compativeis__marca = filters.CharFilter(method='filter_by_marca_sinonimos')
    
    # Filtro para a relação ForeignKey com Category utilizando o ID numérico
    category = filters.NumberFilter(
        field_name='category_id',
        lookup_expr='exact'
    )

    class Meta:
        model = Part
        fields = ['veiculos_compativeis__marca', 'category']

    def filter_by_marca_sinonimos(self, queryset, name, value):
        if not value:
            return queryset.order_by('id')

        value_lower = value.lower()
        lista_sinonimos = None

        # Percorre o dicionário para encontrar a lista correspondente ao termo enviado
        for chave, sinonimos in MARCAS_SINONIMOS.items():
            if value_lower == chave or value_lower in sinonimos:
                lista_sinonimos = sinonimos
                break

        # Se encontrou o grupo de sinônimos, aplica a busca tolerante (__icontains)
        if lista_sinonimos:
            query = Q()
            for sinonimo in lista_sinonimos:
                # Usa __icontains para tolerar espaços extras ou variações de texto na importação
                query |= Q(veiculos_compativeis__marca__icontains=sinonimo)
            
            # .distinct() evita duplicados e .order_by('id') resolve o UnorderedObjectListWarning do DRF
            return queryset.filter(query).distinct().order_by('id')

        # Caso o termo enviado não esteja mapeado, faz uma busca direta parcial por segurança
        return queryset.filter(veiculos_compativeis__marca__icontains=value).distinct().order_by('id')