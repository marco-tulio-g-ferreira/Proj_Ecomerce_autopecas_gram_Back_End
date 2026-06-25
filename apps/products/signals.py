import os
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Part, Estoque, LocalEstoque

# --- 1. CRIAÇÃO DE ESTOQUE (Mantido) ---
@receiver(post_save, sender=Part)
def configurar_novo_produto(sender, instance, created, **kwargs):
    if created:
        local, _ = LocalEstoque.objects.get_or_create(
            nome_local="Padrão",
            defaults={'prateleira': 'A1', 'box': 'B1'}
        )
        Estoque.objects.create(
            produto=instance,
            local=local,
            quantidade=0,
            custo=0,
            preco=0
        )

# --- 2. DELEÇÃO DO ARQUIVO (Ao remover o produto) ---
@receiver(post_delete, sender=Part)
def delete_image_on_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

# --- 3. LIMPEZA DO ARQUIVO (Ao editar/remover imagem) ---
@receiver(pre_save, sender=Part)
def delete_image_on_change(sender, instance, **kwargs):
    # Se for um novo produto, não faz nada
    if not instance.pk:
        return False
    
    try:
        # Busca o objeto antigo no banco de dados
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return False

    # Se a imagem mudou ou está sendo setada como vazia
    if old_instance.image and old_instance.image != instance.image:
        if os.path.isfile(old_instance.image.path):
            os.remove(old_instance.image.path)