"""
extrator_ifc.py  —  QuantAI
============================
Extração de quantitativos arquitetônicos calibrada para modelos IFC4 do Revit.

Correções aplicadas após análise do modelo real (3466.24-ARQ):
  1. Área: propriedade chama '\\X\\C1rea' (encoding IFC para "Área") — buscamos
     pelo valor wrappedValue de qualquer IFCAREAMEASURE no Pset do elemento.
  2. Louças: modelo usa IfcFlowTerminal (IFC4), não IfcSanitaryTerminal.
     Classificamos por palavra-chave no nome: bacia, lavatório, cuba, chuveiro.
  3. Forros: 34 IfcCovering .CEILING. com área em Pset genérico.
  4. Pisos/paredes: não há IfcCovering de piso neste modelo —
     extraímos de IfcSlab .FLOOR. (área) e IfcWall (área de face).
"""

import re
import ifcopenshell
import pandas as pd

try:
    import ifcopenshell.geom as ifc_geom
    import numpy as np
    GEOM_OK = True
except ImportError:
    GEOM_OK = False

SINAPI_MAP = {
    "piso_ceramico":   "87549",
    "parede_ceramico": "87285",
    "forro_gesso":     "88496",
    "rodape":          "74209",
    "porta_madeira":   "72056",
    "janela_aluminio": "72067",
    "bacia":           "83513",
    "cuba":            "83513",
    "lavatorio":       "83513",
    "chuveiro":        "83513",
    "impermeab_manta": "86893",
}


# ── Pavimento ─────────────────────────────────────────────────────────────────
def _pavimento(elem, modelo) -> str:
    try:
        for rel in modelo.by_type("IfcRelContainedInSpatialStructure"):
            if elem in rel.RelatedElements:
                s = rel.RelatingStructure
                if s.is_a("IfcBuildingStorey"):
                    return s.Name or "Sem pavimento"
    except Exception:
        pass
    return "Não identificado"


# ── Área: varre TODOS os Psets procurando qualquer IfcAreaMeasure ─────────────
def _area(elem) -> float:
    """
    Estratégia ampliada:
    1. IfcElementQuantity → IfcQuantityArea (método padrão IFC)
    2. IfcPropertySet     → IfcPropertySingleValue com valor IFCAREAMEASURE
       (inclui '\\X\\C1rea' do Revit e qualquer outro nome)
    """
    try:
        for rel in elem.IsDefinedBy:
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pset = rel.RelatingPropertyDefinition

            # Método 1: IfcElementQuantity
            if pset.is_a("IfcElementQuantity"):
                for q in pset.Quantities:
                    if q.is_a("IfcQuantityArea"):
                        v = q.AreaValue
                        if v and float(v) > 0:
                            return float(v)

            # Método 2: IfcPropertySet — qualquer propriedade com AreaMeasure
            if pset.is_a("IfcPropertySet"):
                for prop in pset.HasProperties:
                    if not prop.is_a("IfcPropertySingleValue"):
                        continue
                    val = getattr(prop, "NominalValue", None)
                    if val is None:
                        continue
                    # Aceita qualquer IfcAreaMeasure independente do nome
                    if val.is_a("IfcAreaMeasure"):
                        v = val.wrappedValue
                        if v and float(v) > 0:
                            return float(v)
    except Exception:
        pass
    return 0.0


def _comprimento(elem) -> float:
    try:
        for rel in elem.IsDefinedBy:
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pset = rel.RelatingPropertyDefinition
            if pset.is_a("IfcElementQuantity"):
                for q in pset.Quantities:
                    if q.is_a("IfcQuantityLength"):
                        v = q.LengthValue
                        if v and float(v) > 0:
                            return float(v)
            if pset.is_a("IfcPropertySet"):
                for prop in pset.HasProperties:
                    if not prop.is_a("IfcPropertySingleValue"):
                        continue
                    nome = (prop.Name or "").lower()
                    if any(k in nome for k in ("length","comprimento","perimeter")):
                        val = getattr(prop, "NominalValue", None)
                        if val and hasattr(val, "wrappedValue"):
                            v = float(val.wrappedValue)
                            if v > 0:
                                return v
    except Exception:
        pass
    return 0.0


def _predefined_type(elem) -> str:
    try:
        pt = getattr(elem, "PredefinedType", None)
        return str(pt).upper() if pt else ""
    except Exception:
        return ""


# ── Classificação de louças por palavra-chave no nome ─────────────────────────
_LOUCA_KW = [
    (["bacia", "vaso", "wc", "p.505", "sanitaria", "sanit"],
     "Bacia sanitária c/ cx. acoplada", "bacia"),
    (["lavatorio", "lavatório", "l.510", "l.830", "celite_city_lavat"],
     "Lavatório / pia", "lavatorio"),
    (["cuba", "cb_cuba", "semiencaixe"],
     "Cuba de embutir", "cuba"),
    (["chuveiro", "ducha", "1955", "1984"],
     "Chuveiro / ducha", "chuveiro"),
    (["torneira", "registro", "monocromado"],
     "Torneira / registro", "lavatorio"),
    (["tanque"],
     "Tanque de lavar roupa", "lavatorio"),
]

def _classificar_louca(nome: str):
    """Retorna (item_label, cod_key) ou None se não for louça principal."""
    n = nome.lower()
    # Exclui acessórios que não têm código SINAPI de louça
    if any(k in n for k in ["barra apoio", "dispenser", "sifao", "sifão",
                              "valvula", "válvula", "cadeira de banho",
                              "caixa acoplada", "coluna para"]):
        return None
    for keywords, label, cod_key in _LOUCA_KW:
        if any(k in n for k in keywords):
            return label, cod_key
    return None


# ── Extração principal ────────────────────────────────────────────────────────
def extrair_quantitativos(caminho_ifc: str, escopo: dict) -> list[dict]:
    modelo = ifcopenshell.open(caminho_ifc)
    rows   = []

    # ── Forros (IfcCovering .CEILING.) ────────────────────────────────────────
    if escopo.get("forros") or escopo.get("revestimentos"):
        for cov in modelo.by_type("IfcCovering"):
            pt  = _predefined_type(cov)
            pav = _pavimento(cov, modelo)

            if pt == "CEILING" and (escopo.get("forros") or escopo.get("revestimentos")):
                area = _area(cov)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["forro_gesso"],
                        "item": "Forro de gesso acartonado",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Forros", "un": "m2", "qtd": round(area, 2),
                    })
            elif pt == "FLOORING" and escopo.get("revestimentos"):
                area = _area(cov)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["piso_ceramico"],
                        "item": "Revestimento cerâmico — piso",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                    })
            elif pt == "CLADDING" and escopo.get("revestimentos"):
                area = _area(cov)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["parede_ceramico"],
                        "item": "Revestimento cerâmico — parede",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                    })
            elif pt == "BASEBOARD" and escopo.get("rodapes"):
                comp = _comprimento(cov)
                if comp > 0:
                    rows.append({
                        "cod": SINAPI_MAP["rodape"],
                        "item": "Rodapé cerâmico",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Revestimentos", "un": "m", "qtd": round(comp, 2),
                    })

    # ── Pisos via IfcSlab .FLOOR. ─────────────────────────────────────────────
    if escopo.get("revestimentos"):
        for slab in modelo.by_type("IfcSlab"):
            pt = _predefined_type(slab)
            if pt in ("FLOOR", "LANDING"):
                pav  = _pavimento(slab, modelo)
                area = _area(slab)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["piso_ceramico"],
                        "item": "Revestimento cerâmico — piso",
                        "ifc": "IfcSlab", "pav": pav,
                        "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                    })
            elif pt == "ROOF" and escopo.get("impermeab"):
                pav  = _pavimento(slab, modelo)
                area = _area(slab)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["impermeab_manta"],
                        "item": "Impermeabilização — manta asfáltica",
                        "ifc": "IfcSlab", "pav": pav,
                        "cat": "Impermeab.", "un": "m2", "qtd": round(area * 1.10, 2),
                    })

    # ── Paredes via IfcWall ────────────────────────────────────────────────────
    if escopo.get("revestimentos"):
        for wall in modelo.by_type("IfcWall"):
            pav  = _pavimento(wall, modelo)
            area = _area(wall)
            if area > 0:
                rows.append({
                    "cod": SINAPI_MAP["parede_ceramico"],
                    "item": "Revestimento cerâmico — parede",
                    "ifc": "IfcWall", "pav": pav,
                    "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                })

    # ── Esquadrias ─────────────────────────────────────────────────────────────
    if escopo.get("esquadrias"):
        for door in modelo.by_type("IfcDoor"):
            pav = _pavimento(door, modelo)
            rows.append({
                "cod": SINAPI_MAP["porta_madeira"],
                "item": "Porta de madeira completa",
                "ifc": "IfcDoor", "pav": pav,
                "cat": "Esquadrias", "un": "un", "qtd": 1,
            })
        for win in modelo.by_type("IfcWindow"):
            pav = _pavimento(win, modelo)
            rows.append({
                "cod": SINAPI_MAP["janela_aluminio"],
                "item": "Janela de alumínio — correr",
                "ifc": "IfcWindow", "pav": pav,
                "cat": "Esquadrias", "un": "un", "qtd": 1,
            })

    # ── Louças via IfcFlowTerminal (IFC4 Revit) ───────────────────────────────
    if escopo.get("loucas"):
        for ft in modelo.by_type("IfcFlowTerminal"):
            nome = (getattr(ft, "Name", "") or "").strip()
            # Remove prefixo de grupo (ex: "Peças hidrossanitárias : Deca_...")
            nome_limpo = nome.split(":")[-1].strip() if ":" in nome else nome
            resultado = _classificar_louca(nome_limpo) or _classificar_louca(nome)
            if resultado:
                item_label, cod_key = resultado
                pav = _pavimento(ft, modelo)
                rows.append({
                    "cod": SINAPI_MAP[cod_key],
                    "item": item_label,
                    "ifc": "IfcFlowTerminal", "pav": pav,
                    "cat": "Louças", "un": "un", "qtd": 1,
                })

    # ── Consolidação ──────────────────────────────────────────────────────────
    if not rows:
        return rows

    df = pd.DataFrame(rows)
    df_agg = (
        df.groupby(["cod","item","ifc","pav","cat","un"], as_index=False)
        .agg(qtd=("qtd","sum"))
    )
    df_agg["qtd"] = df_agg["qtd"].round(2)
    return df_agg.to_dict("records")
