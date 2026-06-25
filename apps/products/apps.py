from django.apps import AppConfig

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'

    def ready(self):
        from django.contrib import admin
        # Muda o título da página e do cabeçalho do Django Admin
        admin.site.site_header = "Auto-Peças Gramense - ERP"
        admin.site.site_title = "Gramense Admin"
        admin.site.index_title = "Engenharia de Produto & Frotas"
        # Registra os signals
        import apps.products.signals