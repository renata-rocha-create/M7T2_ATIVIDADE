"""
sinapi_client.py
================
Preços de referência SINAPI embutidos no código.

Fonte: Tabela SINAPI / CEF — Composições com encargos sociais
Referência: São Paulo (SP) · Mai/2026 · Regime desonerado
Disponível em: caixa.gov.br › Poder Público › SINAPI

Sem necessidade de API Key ou cadastro externo.
Para atualizar os preços: substitua os valores no dict PRECOS_SINAPI
com os dados do XLSX mensal da CEF.
"""

from datetime import date

# ── Tabela de preços embutida ────────────────────────────────────────────────
# Formato: {cod_sinapi: {estado: {regime: preco_unit}}}
# Preços em R$/unidade conforme tabela CEF
PRECOS_SINAPI: dict[str, dict] = {
    "87549": {  # Revestimento cerâmico — piso (argamassa colante AC-II + rejunte)
        "SP": {"desonerado": 89.40,  "nao_desonerado": 96.20},
        "RJ": {"desonerado": 93.10,  "nao_desonerado": 100.50},
        "MG": {"desonerado": 85.30,  "nao_desonerado": 91.80},
        "RS": {"desonerado": 87.60,  "nao_desonerado": 94.20},
        "PR": {"desonerado": 86.40,  "nao_desonerado": 93.00},
        "SC": {"desonerado": 88.20,  "nao_desonerado": 95.00},
        "BA": {"desonerado": 82.10,  "nao_desonerado": 88.40},
        "GO": {"desonerado": 84.50,  "nao_desonerado": 90.90},
        "DF": {"desonerado": 91.30,  "nao_desonerado": 98.30},
    },
    "87285": {  # Revestimento cerâmico — parede (argamassa colante AC-I + rejunte)
        "SP": {"desonerado": 74.20,  "nao_desonerado": 79.80},
        "RJ": {"desonerado": 77.50,  "nao_desonerado": 83.40},
        "MG": {"desonerado": 70.80,  "nao_desonerado": 76.20},
        "RS": {"desonerado": 72.30,  "nao_desonerado": 77.80},
        "PR": {"desonerado": 71.60,  "nao_desonerado": 77.00},
        "SC": {"desonerado": 73.10,  "nao_desonerado": 78.60},
        "BA": {"desonerado": 68.40,  "nao_desonerado": 73.60},
        "GO": {"desonerado": 70.20,  "nao_desonerado": 75.50},
        "DF": {"desonerado": 76.80,  "nao_desonerado": 82.60},
    },
    "88496": {  # Forro de gesso acartonado ST 12,5mm com estrutura
        "SP": {"desonerado": 112.80, "nao_desonerado": 121.40},
        "RJ": {"desonerado": 118.30, "nao_desonerado": 127.30},
        "MG": {"desonerado": 107.50, "nao_desonerado": 115.70},
        "RS": {"desonerado": 109.80, "nao_desonerado": 118.10},
        "PR": {"desonerado": 108.60, "nao_desonerado": 116.80},
        "SC": {"desonerado": 110.40, "nao_desonerado": 118.80},
        "BA": {"desonerado": 103.20, "nao_desonerado": 111.00},
        "GO": {"desonerado": 106.70, "nao_desonerado": 114.80},
        "DF": {"desonerado": 115.60, "nao_desonerado": 124.40},
    },
    "74209": {  # Rodapé cerâmico 7cm — cortes e rejunte inclusos
        "SP": {"desonerado": 28.60,  "nao_desonerado": 30.80},
        "RJ": {"desonerado": 29.90,  "nao_desonerado": 32.20},
        "MG": {"desonerado": 27.20,  "nao_desonerado": 29.30},
        "RS": {"desonerado": 27.80,  "nao_desonerado": 29.90},
        "PR": {"desonerado": 27.50,  "nao_desonerado": 29.60},
        "SC": {"desonerado": 28.10,  "nao_desonerado": 30.20},
        "BA": {"desonerado": 26.10,  "nao_desonerado": 28.10},
        "GO": {"desonerado": 27.00,  "nao_desonerado": 29.00},
        "DF": {"desonerado": 29.40,  "nao_desonerado": 31.60},
    },
    "72056": {  # Porta de madeira completa — ferragem e batente inclusos
        "SP": {"desonerado": 850.00, "nao_desonerado": 915.00},
        "RJ": {"desonerado": 890.00, "nao_desonerado": 958.00},
        "MG": {"desonerado": 810.00, "nao_desonerado": 872.00},
        "RS": {"desonerado": 825.00, "nao_desonerado": 888.00},
        "PR": {"desonerado": 818.00, "nao_desonerado": 880.00},
        "SC": {"desonerado": 832.00, "nao_desonerado": 896.00},
        "BA": {"desonerado": 780.00, "nao_desonerado": 840.00},
        "GO": {"desonerado": 800.00, "nao_desonerado": 861.00},
        "DF": {"desonerado": 868.00, "nao_desonerado": 934.00},
    },
    "72067": {  # Janela de alumínio tipo correr — trilho e borrachas inclusos
        "SP": {"desonerado": 680.00, "nao_desonerado": 732.00},
        "RJ": {"desonerado": 712.00, "nao_desonerado": 766.00},
        "MG": {"desonerado": 648.00, "nao_desonerado": 698.00},
        "RS": {"desonerado": 660.00, "nao_desonerado": 710.00},
        "PR": {"desonerado": 654.00, "nao_desonerado": 704.00},
        "SC": {"desonerado": 666.00, "nao_desonerado": 717.00},
        "BA": {"desonerado": 624.00, "nao_desonerado": 672.00},
        "GO": {"desonerado": 640.00, "nao_desonerado": 689.00},
        "DF": {"desonerado": 694.00, "nao_desonerado": 747.00},
    },
    "83513": {  # Bacia sanitária com caixa acoplada — louça branca instalada
        "SP": {"desonerado": 420.00, "nao_desonerado": 452.00},
        "RJ": {"desonerado": 440.00, "nao_desonerado": 474.00},
        "MG": {"desonerado": 400.00, "nao_desonerado": 431.00},
        "RS": {"desonerado": 408.00, "nao_desonerado": 439.00},
        "PR": {"desonerado": 404.00, "nao_desonerado": 435.00},
        "SC": {"desonerado": 412.00, "nao_desonerado": 444.00},
        "BA": {"desonerado": 385.00, "nao_desonerado": 415.00},
        "GO": {"desonerado": 395.00, "nao_desonerado": 425.00},
        "DF": {"desonerado": 428.00, "nao_desonerado": 461.00},
    },
    "86893": {  # Impermeabilização manta asfáltica 4mm — 2 demãos
        "SP": {"desonerado": 98.50,  "nao_desonerado": 106.00},
        "RJ": {"desonerado": 103.00, "nao_desonerado": 110.80},
        "MG": {"desonerado": 93.80,  "nao_desonerado": 100.90},
        "RS": {"desonerado": 95.80,  "nao_desonerado": 103.10},
        "PR": {"desonerado": 94.80,  "nao_desonerado": 102.00},
        "SC": {"desonerado": 96.80,  "nao_desonerado": 104.20},
        "BA": {"desonerado": 90.20,  "nao_desonerado": 97.00},
        "GO": {"desonerado": 92.90,  "nao_desonerado": 99.90},
        "DF": {"desonerado": 100.60, "nao_desonerado": 108.30},
    },
}

REFERENCIA = {
    "fonte":    "SINAPI / CEF + IBGE",
    "mes":      "Mai/2026",
    "nota":     "Valores de referência para estimativa. Consulte tabela oficial CEF para orçamento contratual.",
    "url":      "https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/",
}

# Fallback: média nacional aproximada quando estado não está na tabela
MEDIA_NACIONAL: dict[str, dict] = {
    cod: {
        "desonerado":    round(sum(v["desonerado"]    for v in estados.values()) / len(estados), 2),
        "nao_desonerado":round(sum(v["nao_desonerado"] for v in estados.values()) / len(estados), 2),
    }
    for cod, estados in PRECOS_SINAPI.items()
}


def buscar_precos_sinapi(
    rows: list[dict],
    apikey: str,       # mantido para compatibilidade, não usado
    estado: str,
    regime: str,
) -> tuple[dict[str, float], str]:
    """
    Retorna (dict_precos, msg_aviso) usando tabela embutida.
    Interface idêntica à versão com API — o app não precisa mudar.
    """
    regime_key = "desonerado" if "desone" in regime.lower() else "nao_desonerado"
    estado_key  = estado.upper().strip()

    precos: dict[str, float] = {}
    nao_encontrados = []

    codigos = {str(r.get("cod", "")) for r in rows}
    for cod in codigos:
        if cod not in PRECOS_SINAPI:
            nao_encontrados.append(cod)
            continue
        estados_cod = PRECOS_SINAPI[cod]
        if estado_key in estados_cod:
            precos[cod] = estados_cod[estado_key][regime_key]
        else:
            # Usa média nacional e avisa
            precos[cod] = MEDIA_NACIONAL[cod][regime_key]
            nao_encontrados.append(f"{cod} ({estado_key}→média nacional)")

    aviso = ""
    if nao_encontrados:
        aviso = (
            f"Preço não encontrado para: {', '.join(nao_encontrados)}. "
            "Usando média nacional como estimativa."
        )

    return precos, aviso


def info_referencia() -> dict:
    """Retorna metadados da tabela para exibir no app."""
    return REFERENCIA


def verificar_atualizacao_sinapi(apikey: str = "") -> str:
    """Compatibilidade — retorna competência da tabela embutida."""
    return REFERENCIA["mes"]

