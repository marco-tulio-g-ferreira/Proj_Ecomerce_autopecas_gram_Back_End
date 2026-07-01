from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Part, Estoque, LocalEstoque

# Variável para cache do local, evitando consultas repetidas ao banco
_LOCAL_PADRAO = None

def get_local_padrao():
    """Retorna o local padrão, criando-o se não existir, e mantendo em cache."""
    global _LOCAL_PADRAO
    if _LOCAL_PADRAO is None:
        _LOCAL_PADRAO, _ = LocalEstoque.objects.get_or_create(
            nome_local="Padrão",
            defaults={'prateleira': 'A1', 'box': 'B1'}
        )
    return _LOCAL_PADRAO

# --- 1. CRIAÇÃO DE ESTOQUE ---
@receiver(post_save, sender=Part)
def configurar_novo_produto(sender, instance, created, **kwargs):
    if created:
        # Usa o cache para evitar SELECT desnecessário
        local = get_local_padrao()
        
        # Criamos o estoque inicial
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
        storage = instance.image.storage
        if storage.exists(instance.image.name):
            storage.delete(instance.image.name)

# --- 3. LIMPEZA DO ARQUIVO (Ao editar/remover imagem) ---
@receiver(pre_save, sender=Part)
def delete_image_on_change(sender, instance, **kwargs):
    # Se for um novo produto, não faz nada
    if not instance.pk:
        return

    try:
        # Busca o objeto antigo no banco para comparar
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    # Se a imagem mudou ou está sendo setada como vazia, removemos a antiga
    if old_instance.image and old_instance.image != instance.image:
        storage = old_instance.image.storage
        
        # Verifica se o arquivo antigo realmente existe no storage antes de deletar
        if storage.exists(old_instance.image.name):
            storage.delete(old_instance.image.name)