"""
extrator_ifc.py
===============
Extração de quantitativos arquitetônicos de arquivo IFC usando IfcOpenShell.

Entidades mapeadas:
    IfcCovering         → revestimentos (piso, parede, teto, rodapé)
    IfcDoor             → portas
    IfcWindow           → janelas
    IfcSanitaryTerminal → louças e metais
    IfcSlab (ROOF)      → impermeabilização
    IfcSpace            → para identificar nome do ambiente/cômodo
    IfcBuildingStorey   → para nomear pavimento

Cada linha retornada é um dict compatível com o DataFrame principal do app.
"""

import ifcopenshell
import ifcopenshell.util.element as ifc_util


# ── Mapeamento de código SINAPI por tipo de elemento ──────────────────────────
# Em produção: pode ser alimentado por uma planilha externa ou pela API SINAPI.
SINAPI_MAP = {
    "piso_ceramico":  "87549",
    "parede_ceramico":"87285",
    "forro_gesso":    "88496",
    "rodape":         "74209",
    "porta_madeira":  "72056",
    "janela_aluminio":"72067",
    "bacia":          "83513",
    "cuba":           "83513",
    "lavatorio":      "83513",
    "chuveiro":       "83513",
    "impermeab_manta":"86893",
    "default":        "00000",
}


def _nome_pavimento(elemento, modelo) -> str:
    """Retorna o nome do IfcBuildingStorey associado ao elemento."""
    try:
        for rel in modelo.by_type("IfcRelContainedInSpatialStructure"):
            if elemento in rel.RelatedElements:
                storey = rel.RelatingStructure
                if storey.is_a("IfcBuildingStorey"):
                    return storey.Name or "Sem pavimento"
    except Exception:
        pass
    return "Não identificado"


def _area_liquida(elemento) -> float:
    """Tenta extrair área líquida do Pset de quantidade."""
    try:
        for rel in elemento.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcElementQuantity"):
                    for q in pset.Quantities:
                        if q.is_a("IfcQuantityArea"):
                            if "Net" in q.Name or "net" in q.Name:
                                return float(q.AreaValue)
                            if "Gross" in q.Name or "gross" in q.Name:
                                return float(q.AreaValue)
    except Exception:
        pass
    return 0.0


def _comprimento(elemento) -> float:
    """Tenta extrair comprimento do Pset de quantidade."""
    try:
        for rel in elemento.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcElementQuantity"):
                    for q in pset.Quantities:
                        if q.is_a("IfcQuantityLength"):
                            return float(q.LengthValue)
    except Exception:
        pass
    return 0.0


def _predefined_type(elemento) -> str:
    """Retorna o PredefinedType como string uppercase ou vazio."""
    try:
        pt = getattr(elemento, "PredefinedType", None)
        return str(pt).upper() if pt else ""
    except Exception:
        return ""


def extrair_quantitativos(caminho_ifc: str, escopo: dict) -> list[dict]:
    """
    Lê o arquivo IFC e retorna lista de dicts com os quantitativos
    de arquitetura conforme o escopo selecionado.

    Parâmetros
    ----------
    caminho_ifc : str
        Caminho local do arquivo .ifc (já salvo em disco pelo Streamlit).
    escopo : dict
        Flags booleanas: revestimentos, esquadrias, loucas, rodapes,
        forros, impermeab.

    Retorna
    -------
    list[dict]
        Cada dict tem: cod, item, ifc, pav, cat, un, qtd
    """
    modelo = ifcopenshell.open(caminho_ifc)
    rows = []

    # ── Revestimentos ──────────────────────────────────────────────────────────
    if escopo.get("revestimentos") or escopo.get("rodapes") or escopo.get("forros"):
        for cov in modelo.by_type("IfcCovering"):
            pt = _predefined_type(cov)
            pav = _nome_pavimento(cov, modelo)

            if pt in ("FLOORING",) and escopo.get("revestimentos"):
                area = _area_liquida(cov)
                if area > 0:
                    rows.append({
                        "cod":  SINAPI_MAP["piso_ceramico"],
                        "item": "Revestimento cerâmico — piso",
                        "ifc":  "IfcCovering",
                        "pav":  pav,
                        "cat":  "Revestimentos",
                        "un":   "m2",
                        "qtd":  round(area, 2),
                    })

            elif pt in ("CLADDING",) and escopo.get("revestimentos"):
                area = _area_liquida(cov)
                if area > 0:
                    rows.append({
                        "cod":  SINAPI_MAP["parede_ceramico"],
                        "item": "Revestimento cerâmico — parede",
                        "ifc":  "IfcCovering",
                        "pav":  pav,
                        "cat":  "Revestimentos",
                        "un":   "m2",
                        "qtd":  round(area, 2),
                    })

            elif pt in ("CEILING",) and escopo.get("forros"):
                area = _area_liquida(cov)
                if area > 0:
                    rows.append({
                        "cod":  SINAPI_MAP["forro_gesso"],
                        "item": "Forro de gesso acartonado",
                        "ifc":  "IfcCovering",
                        "pav":  pav,
                        "cat":  "Forros",
                        "un":   "m2",
                        "qtd":  round(area, 2),
                    })

            elif pt in ("BASEBOARD",) and escopo.get("rodapes"):
                comp = _comprimento(cov)
                if comp > 0:
                    rows.append({
                        "cod":  SINAPI_MAP["rodape"],
                        "item": "Rodapé cerâmico",
                        "ifc":  "IfcCovering",
                        "pav":  pav,
                        "cat":  "Revestimentos",
                        "un":   "m",
                        "qtd":  round(comp, 2),
                    })

    # ── Esquadrias ─────────────────────────────────────────────────────────────
    if escopo.get("esquadrias"):
        for door in modelo.by_type("IfcDoor"):
            pav = _nome_pavimento(door, modelo)
            rows.append({
                "cod":  SINAPI_MAP["porta_madeira"],
                "item": "Porta de madeira completa",
                "ifc":  "IfcDoor",
                "pav":  pav,
                "cat":  "Esquadrias",
                "un":   "un",
                "qtd":  1,
            })

        for win in modelo.by_type("IfcWindow"):
            pav = _nome_pavimento(win, modelo)
            rows.append({
                "cod":  SINAPI_MAP["janela_aluminio"],
                "item": "Janela de alumínio — correr",
                "ifc":  "IfcWindow",
                "pav":  pav,
                "cat":  "Esquadrias",
                "un":   "un",
                "qtd":  1,
            })

    # ── Louças sanitárias ──────────────────────────────────────────────────────
    if escopo.get("loucas"):
        tipo_louca = {
            "WC":       ("Bacia sanitária c/ cx. acoplada", "bacia"),
            "SINK":     ("Cuba de embutir (lavatório)",     "cuba"),
            "SHOWER":   ("Chuveiro / ducha",                "chuveiro"),
            "BATH":     ("Banheira",                        "lavatorio"),
            "WASHBASIN":("Lavatório suspenso",              "lavatorio"),
        }
        for san in modelo.by_type("IfcSanitaryTerminal"):
            pt = _predefined_type(san)
            pav = _nome_pavimento(san, modelo)
            item_label, cod_key = tipo_louca.get(pt, ("Louça sanitária", "bacia"))
            rows.append({
                "cod":  SINAPI_MAP[cod_key],
                "item": item_label,
                "ifc":  "IfcSanitaryTerminal",
                "pav":  pav,
                "cat":  "Louças",
                "un":   "un",
                "qtd":  1,
            })

    # ── Impermeabilização ──────────────────────────────────────────────────────
    if escopo.get("impermeab"):
        for slab in modelo.by_type("IfcSlab"):
            pt = _predefined_type(slab)
            if pt == "ROOF":
                pav = _nome_pavimento(slab, modelo)
                area = _area_liquida(slab)
                if area > 0:
                    area_c_margem = round(area * 1.10, 2)
                    rows.append({
                        "cod":  SINAPI_MAP["impermeab_manta"],
                        "item": "Impermeabilização — manta asfáltica",
                        "ifc":  "IfcSlab",
                        "pav":  pav,
                        "cat":  "Impermeab.",
                        "un":   "m2",
                        "qtd":  area_c_margem,
                    })

    # ── Consolidação: agrupa mesmos itens no mesmo pavimento ──────────────────
    import pandas as pd
    if not rows:
        return rows

    df = pd.DataFrame(rows)
    df_agg = (
        df.groupby(["cod", "item", "ifc", "pav", "cat", "un"], as_index=False)
        .agg(qtd=("qtd", "sum"))
    )
    df_agg["qtd"] = df_agg["qtd"].round(2)
    return df_agg.to_dict("records")
