import uuid
import django_filters
from rest_framework import viewsets, views, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count, F
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
import threading

# Imports locais
from .models import Category, Veiculo, Part, Estoque
from .serializers import AutoPartSerializer, CategorySerializer, VehicleCompatibilitySerializer
from .constants import MARCAS_SINONIMOS
from .services import processar_importacao_background, gerar_cobranca_pix

# --- Configurações de paginação ---
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# --- Classes de Filtro ---
class PartFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="estoque__preco", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="estoque__preco", lookup_expr='lte')
    min_stock = django_filters.NumberFilter(field_name="estoque__quantidade", lookup_expr='gte')

    class Meta:
        model = Part
        fields = ['category']

class DebugTokenAuthentication(TokenAuthentication):
    """Autenticação para ambiente de debug, substituir em produção por algo seguro."""
    def authenticate(self, request):
        return super().authenticate(request)

# --- ViewSets ---

class AutoPartViewSet(viewsets.ModelViewSet):
    serializer_class = AutoPartSerializer
    pagination_class = StandardResultsSetPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'codigo_oem', 'description']
    filterset_class = PartFilter
    ordering_fields = ['estoque__quantidade', 'estoque__preco', 'id', 'name', 'sku']

    def get_queryset(self):
        queryset = Part.objects.all().select_related('estoque', 'category').order_by('id')
        brand_key = self.request.query_params.get('veiculos_compativeis__marca')
        if brand_key:
            sinonimos = MARCAS_SINONIMOS.get(brand_key.lower(), [brand_key])
            queryset = queryset.filter(veiculos_compativeis__marca__in=sinonimos)
        return queryset

    @action(detail=True, methods=['patch'])
    def update_stock(self, request, pk=None):
        try:
            ajuste = request.data.get('quantidade')
            if ajuste is None:
                return Response({"error": "Campo 'quantidade' obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

            # Atualização atômica no banco de dados
            updated_count = Estoque.objects.filter(produto_id=pk).update(
                quantidade=F('quantidade') + int(float(ajuste))
            )

            if updated_count == 0:
                return Response({"error": "Estoque não encontrado para este produto"}, status=status.HTTP_404_NOT_FOUND)

            estoque_instance = Estoque.objects.get(produto_id=pk)
            return Response({"status": "sucesso", "estoque": int(estoque_instance.quantidade)})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_update(self, serializer):
        # Lógica para remover imagem se o front enviar 'remove_image'
        if self.request.data.get('remove_image') == 'true':
            # Remove a imagem fisicamente do modelo
            instance = serializer.instance
            instance.image.delete(save=False)
            serializer.save(image=None)
        else:
            serializer.save()

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

class VehicleCompatibilityViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all()
    serializer_class = VehicleCompatibilitySerializer

# --- Views de API (Funcionalidades Extras) ---

class PixGerarView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        valor = request.data.get('valor')
        if not valor:
            return Response({"error": "Valor é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            dados_pix = gerar_cobranca_pix(valor)
            return Response(dados_pix, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryStatsView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        stats = Category.objects.annotate(count=Count('parts')).values('id', 'name', 'count')
        return Response(list(stats))

class ImportarProdutosView(views.APIView):
    authentication_classes = [DebugTokenAuthentication]
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        arquivo = request.FILES.get('file')
        if not arquivo:
            return Response({"error": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)

        task_id = str(uuid.uuid4())
        cache.set(f"import_progress_{task_id}", {"progress": 0, "message": "Iniciando processamento..."}, timeout=3600)
        
        # Execução em background
        threading.Thread(
            target=processar_importacao_background, 
            args=(arquivo.read(), arquivo.name, task_id)
        ).start()

        return Response({"task_id": task_id}, status=status.HTTP_202_ACCEPTED)

    def get(self, request):
        task_id = request.query_params.get('task_id')
        data = cache.get(f"import_progress_{task_id}")
        if not data:
            return Response({"error": "Tarefa não encontrada ou expirada"}, status=status.HTTP_404_NOT_FOUND)
        return Response(data)

# --- Views de Autenticação e Usuário ---

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key, 
                    "user": {"email": user.email, "name": user.first_name, "role": "admin" if user.is_staff else "user"}
                })
            return Response({"error": "Senha incorreta"}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email e senha são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Este e-mail já está cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        return Response({'success': True, 'message': 'Usuário criado com sucesso!'}, status=status.HTTP_201_CREATED)

class ProfileUpdateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        user = request.user
        user.first_name = request.data.get('name', user.first_name)
        user.email = request.data.get('email', user.email)
        user.save()
        return Response({"name": user.first_name, "email": user.email})

class ChangePasswordView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        if not password:
            return Response({"error": "A senha é obrigatória"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        user.set_password(password)
        user.save()
        return Response({"status": "sucesso", "message": "Senha alterada com sucesso!"})

class RevisaoView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"count": 0, "items": []}, status=status.HTTP_200_OK)