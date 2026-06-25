from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AutoPartViewSet, 
    CategoryViewSet, 
    VehicleCompatibilityViewSet, 
    ImportarProdutosView, 
    LoginView, 
    RegisterView, 
    ProfileUpdateView, 
    CategoryStatsView, 
    ChangePasswordView,
    RevisaoView
)

# Configuração do Router
router = DefaultRouter()
router.register(r'products', AutoPartViewSet, basename='products')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'veiculos', VehicleCompatibilityViewSet, basename='veiculos')

# Definição das URLs
urlpatterns = [
    # Rotas padrão do Router
    path('', include(router.urls)),
    
    # Rotas customizadas
    path('category/stats/', CategoryStatsView.as_view(), name='category-stats'),
    path('import/', ImportarProdutosView.as_view(), name='importar-produtos'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('revisao/', RevisaoView.as_view(), name='revisao'),
]