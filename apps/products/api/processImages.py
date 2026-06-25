import os
import requests
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

import django
from django.conf import settings

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.products.models import Part

# Pasta de saída dentro de MEDIA_ROOT
OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "imagens", "pecas")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def baixar_converter(url, nome):
    """Baixa uma imagem e salva como JPG."""
    caminho = os.path.join(OUTPUT_DIR, f"{nome}.jpg")

    if os.path.exists(caminho):
        print(f"⏩ {nome} já existe, pulando...")
        return nome, True

    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content))
        # Converte para RGB se necessário (PNG com transparência)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(caminho, "JPEG", quality=80)

        # Atualiza o banco com o caminho relativo correto
        relative_path = f"/media/imagens/pecas/{nome}.jpg"
        part = Part.objects.filter(sku=nome).first()
        if part:
            part.image_url = relative_path
            part.save(update_fields=["image_url"])

        print(f"✅ {nome} convertido com sucesso")
        return nome, True
    except Exception as e:
        print(f"❌ Falha ao processar {nome}: {e}")
        return nome, False


def processar_imagens(lista_imagens, max_workers=10):
    """Processa uma lista de (url, nome) e baixa as imagens."""
    sucessos, falhas = 0, 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = [executor.submit(baixar_converter, url, nome) for url, nome in lista_imagens]
        for futuro in as_completed(futuros):
            nome, ok = futuro.result()
            if ok:
                sucessos += 1
            else:
                falhas += 1
    print(f"\n🚀 Processo concluído! Sucessos: {sucessos} | Falhas: {falhas}")


if __name__ == "__main__":
    lista_imagens = [
        ("https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.jpg", "teste1"),
        ("https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg", "teste2"),
    ]
    processar_imagens(lista_imagens, max_workers=10)
