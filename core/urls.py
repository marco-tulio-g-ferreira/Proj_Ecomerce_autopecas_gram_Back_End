from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Importante
from django.conf.urls.static import static # Importante

urlpatterns = [
    path('admin/', admin.site.urls),
    # Inclui todas as rotas definidas dentro de apps.products.urls
    path('api/', include('apps.products.urls')), 
]

# Adicione estas linhas abaixo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)