from rest_framework import serializers
from .models import Part, Category, Veiculo, Estoque
from PIL import Image
import io
from django.core.files.base import ContentFile
import os

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class VehicleCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = ['id', 'marca', 'modelo', 'motor', 'ano']

class AutoPartSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    veiculos_compativeis = serializers.PrimaryKeyRelatedField(
        queryset=Veiculo.objects.all(), many=True, required=False
    )
    # image é write_only para não tentar serializar o objeto de arquivo complexo no GET
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
        # 1. Tenta extrair a imagem do payload
        image_file = validated_data.pop('image', None)

        # 2. Se houver imagem, processa para WebP antes de atualizar
        if image_file:
            try:
                img = Image.open(image_file)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                output = io.BytesIO()
                img.save(output, format='WEBP', quality=85)
                output.seek(0)
                
                nome_base = os.path.splitext(image_file.name)[0]
                instance.image.save(f"{nome_base}.webp", ContentFile(output.read()), save=False)
            except Exception as e:
                raise serializers.ValidationError({"image": f"Erro ao processar imagem: {str(e)}"})

        # 3. Atualiza os demais campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 4. Salva o objeto. Como não tocamos no campo 'image' se não houver arquivo,
        # o Django não disparará o storage (Cloudinary) desnecessariamente.
        instance.save()
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