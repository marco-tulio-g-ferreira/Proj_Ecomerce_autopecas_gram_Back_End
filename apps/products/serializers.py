from rest_framework import serializers
from .models import Part, Category, Veiculo, Estoque
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
        if value > MAX_PRICE_THRESHOLD:
            raise serializers.ValidationError(f"O preço não pode exceder R$ {MAX_PRICE_THRESHOLD}")
        if value < 0:
            raise serializers.ValidationError("O preço não pode ser negativo.")
        return value

class AutoPartSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    veiculos_compativeis = serializers.PrimaryKeyRelatedField(
        queryset=Veiculo.objects.all(), many=True, required=False
    )
    image = serializers.ImageField(required=False, write_only=True)
    
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
        # 1. Extrai a imagem do validated_data para controle manual
        image = validated_data.pop('image', None)

        # 2. Atualiza os campos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 3. Lista de campos que serão alterados
        update_fields = list(validated_data.keys())

        # 4. Só atribui e sinaliza a imagem se ela foi enviada no request
        if image:
            instance.image = image
            update_fields.append('image')
        
        # 5. Salva apenas os campos alterados.
        # Se 'image' não estiver em update_fields, o Django não dispara o pre_save da imagem.
        instance.save(update_fields=update_fields)
        
        return instance

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

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
        return VehicleCompatibilitySerializer(obj.veiculos_compativeis.all(), many=True).data

    def get_price(self, obj):
        return float(obj.estoque.preco) if hasattr(obj, 'estoque') and obj.estoque.preco else 0

    def get_stock(self, obj):
        return obj.estoque.quantidade if hasattr(obj, 'estoque') else 0