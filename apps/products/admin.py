from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Veiculo, Part

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('id', 'marca', 'modelo', 'motor', 'ano', 'chassi')
    list_filter = ('marca', 'ano')
    search_fields = ('modelo', 'chassi')

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'name', 'category', 'peso', 'codigo_oem', 'veiculos_count', 'preview_image')
    list_filter = ('category',)
    search_fields = ('sku', 'name', 'codigo_oem')
    filter_horizontal = ('veiculos_compativeis',)
    readonly_fields = ('preview_image',)

    @admin.display(description="Veículos")
    def veiculos_count(self, obj):
        count = obj.veiculos_compativeis.count()
        return format_html('<b style="color:#2a7;">{}</b>', count) if count else format_html('<span style="color:#999;">0</span>')

    @admin.display(description="Imagem")
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "Sem imagem"