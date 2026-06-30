from rest_framework import serializers
from .models import Part, Category, Veiculo, Estoque
from decimal import Decimal
from .constants import MAX_PRICE_THRESHOLD

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class VehicleCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = ['id', 'marca', 'modelo', 'motor', 'ano']

class EstoqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estoque
        fields = ['quantidade', 'preco', 'custo']

    def validate_preco(self, value):
        """Validação de sanidade para o preço do estoque."""
        if value > MAX_PRICE_THRESHOLD:
            raise serializers.ValidationError(f"O preço não pode exceder R$ {MAX_PRICE_THRESHOLD}")
        if value < 0:
            raise serializers.ValidationError("O preço não pode ser negativo.")
        return value

class AutoPartSerializer(serializers.ModelSerializer):
    # Relacionamentos (Input)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    veiculos_compativeis = serializers.PrimaryKeyRelatedField(
        queryset=Veiculo.objects.all(), many=True, required=False
    )

    # Campo para upload (Write-only)
    image = serializers.ImageField(required=False, write_only=True)

    # Campos calculados e de leitura
    image_url = serializers.SerializerMethodField() 
    category_name = serializers.SerializerMethodField()
    estoque = serializers.SerializerMethodField()
    category_details = serializers.SerializerMethodField()
    veiculos_details = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Part
        fields = [
            'id', 'sku', 'name', 'image', 'image_url', 'description', 'codigo_oem', 'peso', 'dimensoes',
            'is_generic', 'category', 'category_name', 'veiculos_compativeis', 
            'estoque', 'category_details', 'veiculos_details', 'price', 'stock',
        ]

    def update(self, instance, validated_data):
        """
        Sobrescreve o update para garantir que, se nenhuma imagem for enviada,
        o campo image não seja tocado e o método save() do model não tente
        realizar um upload desnecessário.
        """
        # Extraímos a imagem do validated_data, caso ela tenha sido enviada
        image = validated_data.pop('image', None)

        # Atualiza os outros campos normalmente
        instance = super().update(instance, validated_data)

        # Só atualizamos a imagem se o usuário realmente enviou um novo arquivo
        if image:
            instance.image = image
            instance.save()
        
        return instance

    # --- Métodos de Leitura ---
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Sem Categoria"

    def get_estoque(self, obj):
        if hasattr(obj, 'estoque'):
            return {
                "quantidade": obj.estoque.quantidade,
                "preco": float(obj.estoque.preco) if obj.estoque.preco else 0,
                "custo": float(obj.estoque.custo) if obj.estoque.custo else 0,
            }
        return {"quantidade": 0, "preco": 0, "custo": 0}

    def get_category_details(self, obj):
        return CategorySerializer(obj.category).data if obj.category else None

    def get_veiculos_details(self, obj):
        return VehicleCompatibilitySerializer(
            obj.veiculos_compativeis.all(), many=True
        ).data

    def get_price(self, obj):
        if hasattr(obj, 'estoque') and obj.estoque.preco:
            return float(obj.estoque.preco)
        return 0

    def get_stock(self, obj):
        if hasattr(obj, 'estoque'):
            return obj.estoque.quantidade
        return 0