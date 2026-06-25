from decimal import Decimal

MARCAS_SINONIMOS = {
    "vw": ["volkswagen", "vw", "volks"],
    "chevrolet": ["chevrolet", "chev", "gm", "opel"],
    "fiat": ["fiat"],
    "honda": ["honda"],
    "hyundai": ["hyundai"],
    "renault": ["renault"],
    "toyota": ["toyota"],
    "ford": ["ford"],
    "peugeot": ["peugeot", "psa"]
}

CATEGORIAS_MAPEAMENTO = {
    "Lubrificantes": ["ÓLEO", "LUBRIFICANTE", "FLUIDO", "GRAXA"],
    "Sistema de Freio": ["PASTILHA", "DISCO", "FLEXÍVEL DE FREIO", "FLEXIVEL", "FREIO"],
    "Suspensão": ["AMORTECEDOR", "COXIM", "BUCHA", "MOLA", "PIVÔ", "TERMINAL"],
    "Arrefecimento": ["FLANGE", "BOMBA", "TERMOSTATO", "CARCAÇA", "SENSOR", "RADIADOR"],
    "Filtros": ["FILTRO"],
    "Abraçadeiras": ["ABRAÇADEIRA"],
    "Motor": ["JOGO DE ANEL", "PISTÃO", "VELA", "JUNTA"],
    "Elétrica": ["BATERIA", "INTERRUPTOR", "RELÊ", "CABO"],
    "Direção": ["CAIXA DE DIREÇÃO", "BOMBA DE DIREÇÃO"],
}

# Preço máximo aceitável para um item
MAX_PRICE_THRESHOLD = Decimal("50000.00")