"""
extrator_ifc.py
===============
Extração de quantitativos arquitetônicos de arquivo IFC usando IfcOpenShell.

Estratégia de extração de área (em ordem de prioridade):
    1. IfcElementQuantity (Pset de quantidade — mais confiável)
    2. Propriedades nomeadas em Psets genéricos (ex: "Area", "Área", "GrossArea")
    3. Geometria via shape — calcula a maior face plana do sólido (fallback)

Entidades mapeadas:
    IfcCovering         → revestimentos (piso, parede, teto, rodapé)
    IfcDoor             → portas
    IfcWindow           → janelas
    IfcSanitaryTerminal → louças e metais
    IfcSlab (ROOF)      → impermeabilização
    IfcBuildingStorey   → nomeia pavimento
"""

import ifcopenshell
import ifcopenshell.util.shape as ifc_shape

try:
    import ifcopenshell.geom as ifc_geom
    GEOM_DISPONIVEL = True
except ImportError:
    GEOM_DISPONIVEL = False

import numpy as np
import pandas as pd

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

# Nomes de propriedade que podem conter área em Psets genéricos
AREA_PROP_NAMES = {
    "area", "área", "grossarea", "netarea", "gross area", "net area",
    "areabruta", "arealiquida", "floorarea", "wallarea",
}

COMP_PROP_NAMES = {
    "length", "comprimento", "perimeter", "perímetro",
    "grossperimeter", "netperimeter",
}


# ── Helpers de pavimento ──────────────────────────────────────────────────────
def _nome_pavimento(elemento, modelo) -> str:
    try:
        for rel in modelo.by_type("IfcRelContainedInSpatialStructure"):
            if elemento in rel.RelatedElements:
                storey = rel.RelatingStructure
                if storey.is_a("IfcBuildingStorey"):
                    return storey.Name or "Sem pavimento"
    except Exception:
        pass
    return "Não identificado"


# ── Estratégia 1: IfcElementQuantity ─────────────────────────────────────────
def _area_de_pset_quantidade(elemento) -> float:
    try:
        for rel in elemento.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcElementQuantity"):
                    for q in pset.Quantities:
                        if q.is_a("IfcQuantityArea"):
                            val = q.AreaValue
                            if val and float(val) > 0:
                                return float(val)
    except Exception:
        pass
    return 0.0


def _comprimento_de_pset_quantidade(elemento) -> float:
    try:
        for rel in elemento.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcElementQuantity"):
                    for q in pset.Quantities:
                        if q.is_a("IfcQuantityLength"):
                            val = q.LengthValue
                            if val and float(val) > 0:
                                return float(val)
    except Exception:
        pass
    return 0.0


# ── Estratégia 2: Psets genéricos com propriedades nomeadas ──────────────────
def _area_de_psets_genericos(elemento) -> float:
    try:
        for rel in elemento.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcPropertySet"):
                    for prop in pset.HasProperties:
                        nome = (prop.Name or "").lower().replace(" ", "").replace("_", "")
                        if nome in AREA_PROP_NAMES:
                            val = getattr(prop, "NominalValue", None)
                            if val and hasattr(val, "wrappedValue"):
                                v = float(val.wrappedValue)
                                if v > 0:
                                    return v
    except Exception:
        pass
    return 0.0


def _comprimento_de_psets_genericos(elemento) -> float:
    try:
        for rel in elemento.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcPropertySet"):
                    for prop in pset.HasProperties:
                        nome = (prop.Name or "").lower().replace(" ", "").replace("_", "")
                        if nome in COMP_PROP_NAMES:
                            val = getattr(prop, "NominalValue", None)
                            if val and hasattr(val, "wrappedValue"):
                                v = float(val.wrappedValue)
                                if v > 0:
                                    return v
    except Exception:
        pass
    return 0.0


# ── Estratégia 3: Geometria (maior face plana do sólido) ─────────────────────
def _area_de_geometria(elemento, settings) -> float:
    """
    Calcula a área da maior face plana do elemento via tessellação.
    Análogo a medir o polígono mais largo de uma caixa 3D —
    para pisos e paredes isso dá a área de revestimento com boa precisão.
    """
    if not GEOM_DISPONIVEL:
        return 0.0
    try:
        shape = ifc_geom.create_shape(settings, elemento)
        verts = shape.geometry.verts    # lista plana [x,y,z, x,y,z, ...]
        faces = shape.geometry.faces    # lista plana [i,j,k, i,j,k, ...]

        verts_arr = np.array(verts).reshape(-1, 3)
        faces_arr = np.array(faces).reshape(-1, 3)

        maior_area = 0.0
        for tri in faces_arr:
            v0, v1, v2 = verts_arr[tri[0]], verts_arr[tri[1]], verts_arr[tri[2]]
            # Área do triângulo via produto vetorial
            area_tri = np.linalg.norm(np.cross(v1 - v0, v2 - v0)) / 2.0
            maior_area += area_tri

        # Converte de mm² para m² (IFC usa metros por padrão, mas Revit às vezes usa mm)
        # Heurística: se o valor for muito grande, está em mm²
        if maior_area > 10000:
            maior_area = maior_area / 1_000_000

        return round(maior_area, 2) if maior_area > 0 else 0.0
    except Exception:
        return 0.0


def _area_total(elemento, settings) -> float:
    """Tenta as 3 estratégias em sequência, retorna a primeira > 0."""
    area = _area_de_pset_quantidade(elemento)
    if area > 0:
        return area
    area = _area_de_psets_genericos(elemento)
    if area > 0:
        return area
    area = _area_de_geometria(elemento, settings)
    return area


def _comprimento_total(elemento) -> float:
    comp = _comprimento_de_pset_quantidade(elemento)
    if comp > 0:
        return comp
    return _comprimento_de_psets_genericos(elemento)


def _predefined_type(elemento) -> str:
    try:
        pt = getattr(elemento, "PredefinedType", None)
        return str(pt).upper() if pt else ""
    except Exception:
        return ""


# ── Extração principal ────────────────────────────────────────────────────────
def extrair_quantitativos(caminho_ifc: str, escopo: dict) -> list[dict]:
    modelo = ifcopenshell.open(caminho_ifc)

    # Configurações de geometria para o fallback por shape
    settings = None
    if GEOM_DISPONIVEL:
        settings = ifc_geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

    rows = []

    # ── Revestimentos ──────────────────────────────────────────────────────────
    if any([escopo.get("revestimentos"), escopo.get("rodapes"), escopo.get("forros")]):
        for cov in modelo.by_type("IfcCovering"):
            pt  = _predefined_type(cov)
            pav = _nome_pavimento(cov, modelo)

            if pt == "FLOORING" and escopo.get("revestimentos"):
                area = _area_total(cov, settings)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["piso_ceramico"],
                        "item": "Revestimento cerâmico — piso",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                    })

            elif pt == "CLADDING" and escopo.get("revestimentos"):
                area = _area_total(cov, settings)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["parede_ceramico"],
                        "item": "Revestimento cerâmico — parede",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                    })

            elif pt == "CEILING" and escopo.get("forros"):
                area = _area_total(cov, settings)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["forro_gesso"],
                        "item": "Forro de gesso acartonado",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Forros", "un": "m2", "qtd": round(area, 2),
                    })

            elif pt == "BASEBOARD" and escopo.get("rodapes"):
                comp = _comprimento_total(cov)
                if comp > 0:
                    rows.append({
                        "cod": SINAPI_MAP["rodape"],
                        "item": "Rodapé cerâmico",
                        "ifc": "IfcCovering", "pav": pav,
                        "cat": "Revestimentos", "un": "m", "qtd": round(comp, 2),
                    })

            # Sem PredefinedType — tenta inferir pelo nome do tipo
            elif pt in ("", "NOTDEFINED", "USERDEFINED") and escopo.get("revestimentos"):
                nome = (getattr(cov, "Name", "") or "").lower()
                area = _area_total(cov, settings)
                if area > 0:
                    if any(k in nome for k in ("piso", "floor", "pavimento")):
                        rows.append({
                            "cod": SINAPI_MAP["piso_ceramico"],
                            "item": "Revestimento — piso (tipo inferido)",
                            "ifc": "IfcCovering", "pav": pav,
                            "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                        })
                    elif any(k in nome for k in ("parede", "wall", "cladding")):
                        rows.append({
                            "cod": SINAPI_MAP["parede_ceramico"],
                            "item": "Revestimento — parede (tipo inferido)",
                            "ifc": "IfcCovering", "pav": pav,
                            "cat": "Revestimentos", "un": "m2", "qtd": round(area, 2),
                        })
                    elif any(k in nome for k in ("teto", "ceiling", "forro")):
                        rows.append({
                            "cod": SINAPI_MAP["forro_gesso"],
                            "item": "Forro (tipo inferido)",
                            "ifc": "IfcCovering", "pav": pav,
                            "cat": "Forros", "un": "m2", "qtd": round(area, 2),
                        })

    # ── Esquadrias ─────────────────────────────────────────────────────────────
    if escopo.get("esquadrias"):
        for door in modelo.by_type("IfcDoor"):
            pav = _nome_pavimento(door, modelo)
            rows.append({
                "cod": SINAPI_MAP["porta_madeira"],
                "item": "Porta de madeira completa",
                "ifc": "IfcDoor", "pav": pav,
                "cat": "Esquadrias", "un": "un", "qtd": 1,
            })
        for win in modelo.by_type("IfcWindow"):
            pav = _nome_pavimento(win, modelo)
            rows.append({
                "cod": SINAPI_MAP["janela_aluminio"],
                "item": "Janela de alumínio — correr",
                "ifc": "IfcWindow", "pav": pav,
                "cat": "Esquadrias", "un": "un", "qtd": 1,
            })

    # ── Louças ─────────────────────────────────────────────────────────────────
    if escopo.get("loucas"):
        tipo_louca = {
            "WC":        ("Bacia sanitária c/ cx. acoplada", "bacia"),
            "SINK":      ("Cuba de embutir (lavatório)",     "cuba"),
            "SHOWER":    ("Chuveiro / ducha",                "chuveiro"),
            "BATH":      ("Banheira",                        "lavatorio"),
            "WASHBASIN": ("Lavatório suspenso",              "lavatorio"),
        }
        for san in modelo.by_type("IfcSanitaryTerminal"):
            pt  = _predefined_type(san)
            pav = _nome_pavimento(san, modelo)
            item_label, cod_key = tipo_louca.get(pt, ("Louça sanitária", "bacia"))
            rows.append({
                "cod": SINAPI_MAP[cod_key],
                "item": item_label,
                "ifc": "IfcSanitaryTerminal", "pav": pav,
                "cat": "Louças", "un": "un", "qtd": 1,
            })

    # ── Impermeabilização ──────────────────────────────────────────────────────
    if escopo.get("impermeab"):
        for slab in modelo.by_type("IfcSlab"):
            if _predefined_type(slab) == "ROOF":
                pav  = _nome_pavimento(slab, modelo)
                area = _area_total(slab, settings)
                if area > 0:
                    rows.append({
                        "cod": SINAPI_MAP["impermeab_manta"],
                        "item": "Impermeabilização — manta asfáltica",
                        "ifc": "IfcSlab", "pav": pav,
                        "cat": "Impermeab.", "un": "m2",
                        "qtd": round(area * 1.10, 2),
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

