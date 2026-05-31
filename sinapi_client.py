"""
sinapi_client.py
================
Integração com a API SINAPI do Orçamentador (v1.5.1).
Documentação: https://orcamentador.com.br/api/docs

Endpoint principal usado: /orcamento
    - Envia todos os códigos + quantidades em uma única chamada (batch)
    - Formato: C:CODIGO@QUANTIDADE  (C = composição = serviço com MO embutida)
    - Retorna preços por unidade para cada código consultado

Endpoint de apoio: /atualizacao
    - Verifica a data de referência da tabela SINAPI ativa
"""

import requests

BASE_URL = "https://orcamentador.com.br/api"
TIMEOUT  = 20


def buscar_precos_sinapi(
    rows: list[dict],
    apikey: str,
    estado: str,
    regime: str,
) -> dict[str, float]:
    """
    Consulta o endpoint /orcamento com todos os itens em lote.

    Parâmetros
    ----------
    rows    : lista de dicts com campos 'cod' e 'qtd'
    apikey  : chave da API (obtida em orcamentador.com.br/api)
    estado  : sigla do estado (ex: 'SP', 'RJ')
    regime  : 'desonerado' ou 'nao_desonerado'

    Retorna
    -------
    dict {cod_sinapi: preco_unitario (float)}
    Retorna dict vazio se a API não responder ou retornar formato inesperado.
    """
    # Monta a string de itens agrupada por código (evita duplicatas na chamada)
    codigos_qtd: dict[str, float] = {}
    for r in rows:
        cod = str(r["cod"])
        codigos_qtd[cod] = codigos_qtd.get(cod, 0.0) + float(r["qtd"])

    # Formato exigido pela API: C:87549@723.30,C:87285@332.50,...
    itens_str = ",".join(
        f"C:{cod}@{qtd:.2f}" for cod, qtd in codigos_qtd.items()
    )

    params = {
        "apikey": apikey,
        "itens":  itens_str,
        "estado": estado,
        "regime": regime,
    }

    try:
        resp = requests.get(f"{BASE_URL}/orcamento/", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        detail = e.response.text[:200]
        raise RuntimeError(
            f"API SINAPI retornou erro {status}. "
            f"Verifique a API Key e o estado informado. Detalhe: {detail}"
        ) from e
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Não foi possível conectar à API do Orçamentador. "
            "Verifique sua conexão com a internet."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("A API do Orçamentador não respondeu no tempo limite (20s).")
    except ValueError:
        raise RuntimeError("A API retornou uma resposta inválida (não é JSON).")

    # A resposta tem o formato:
    # {"itens": [{"codigo": "87549", "preco": 89.40, "descricao": "...", ...}], "totais": {...}}
    precos: dict[str, float] = {}
    for item in data.get("itens", []):
        cod   = str(item.get("codigo", ""))
        # A API pode retornar o preço em campos diferentes conforme a versão
        preco = (
            item.get("preco")
            or item.get("preco_unitario")
            or item.get("valor")
            or item.get("custo_unitario")
        )
        if cod and preco is not None:
            precos[cod] = float(preco)

    return precos


def verificar_atualizacao_sinapi(apikey: str) -> str:
    """
    Retorna a data de referência da tabela SINAPI ativa na API.
    Útil para exibir ao usuário a competência dos preços consultados.
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/atualizacao/",
            params={"apikey": apikey},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("mes_referencia") or data.get("data") or "—"
    except Exception:
        return "—"
