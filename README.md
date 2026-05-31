# M7T2_ATIVIDADE
 QuantAI — Quantificação Arquitetônica BIM

# QuantAI — Quantificação Arquitetônica BIM

**M7T2 · Zigurat Institute of Technology · Prof. Thomas Takeuchi · Aluna: Renata Rocha**

App Streamlit para extração automatizada de quantitativos arquitetônicos a partir de arquivos IFC, com preços de referência SINAPI embutidos e exportação para Excel formatado.

🔗 **App online:** [m7t2atividade-h2ej63y6xgygcnewgcutyy.streamlit.app](https://m7t2atividade-h2ej63y6xgygcnewgcutyy.streamlit.app)

---

## Estrutura do projeto

```
QuantAI/
├── app.py              # App Streamlit principal
├── extrator_ifc.py     # Extração de quantitativos com IfcOpenShell
├── sinapi_client.py    # Tabela de preços SINAPI embutida (SP, RJ, MG e mais)
├── excel_export.py     # Geração do Excel em memória (3 abas, cores Zigurat)
├── requirements.txt    # Dependências Python
└── README.md
```

---

## Funcionalidades

- **Upload de IFC** — suporta IFC 2x3 e IFC 4 (exportados do Revit, ArchiCAD, Vectorworks)
- **Extração inteligente** — 3 estratégias de leitura de área em cascata:
  1. `IfcElementQuantity` (Pset de quantidade padrão IFC)
  2. Psets genéricos — lê `IfcAreaMeasure` independente do nome da propriedade (inclusive `\X\C1rea` do Revit)
  3. Geometria via `ifcopenshell.geom` como fallback
- **Louças via IfcFlowTerminal** — padrão IFC4 do Revit, classificadas por palavra-chave no nome
- **Preços SINAPI embutidos** — 8 códigos de composição para 9 estados brasileiros, regime desonerado e não desonerado
- **4 visualizações:** tabela de quantitativos com filtros, gráfico de barras por categoria, mapa de calor por pavimento (quantidade e custo), exportação Excel
- **Excel com 3 abas:** Quantitativos, Resumo por Categoria, Critérios Adotados — cores e fontes Zigurat

---

## Entidades IFC mapeadas

| Entidade IFC | PredefinedType | Elemento extraído |
|---|---|---|
| `IfcCovering` | `FLOORING` | Revestimento cerâmico — piso |
| `IfcCovering` | `CLADDING` | Revestimento cerâmico — parede |
| `IfcCovering` | `CEILING` | Forro de gesso acartonado |
| `IfcCovering` | `BASEBOARD` | Rodapé cerâmico |
| `IfcSlab` | `FLOOR` / `LANDING` | Revestimento cerâmico — piso (laje) |
| `IfcSlab` | `ROOF` | Impermeabilização — manta asfáltica |
| `IfcWall` | — | Revestimento cerâmico — parede |
| `IfcDoor` | — | Porta de madeira completa |
| `IfcWindow` | — | Janela de alumínio — correr |
| `IfcFlowTerminal` | nome: bacia / lavatório / cuba / chuveiro | Louças e metais sanitários |

---

## Referência de preços SINAPI

Tabela embutida no código — sem necessidade de API Key ou cadastro externo.

**Fonte:** SINAPI / CEF + IBGE · **Referência:** Mai/2026 · **Regime:** Desonerado e Não desonerado

Códigos de composição utilizados:

| Cód. SINAPI | Descrição |
|---|---|
| 87549 | Revestimento cerâmico — piso (argamassa AC-II + rejunte) |
| 87285 | Revestimento cerâmico — parede (argamassa AC-I + rejunte) |
| 88496 | Forro de gesso acartonado ST 12,5mm com estrutura |
| 74209 | Rodapé cerâmico 7cm — cortes e rejunte inclusos |
| 72056 | Porta de madeira completa — ferragem e batente inclusos |
| 72067 | Janela de alumínio tipo correr — trilho e borrachas inclusos |
| 83513 | Bacia sanitária com caixa acoplada — louça branca instalada |
| 86893 | Impermeabilização — manta asfáltica 4mm, 2 demãos |

Estados disponíveis com preços individualizados: SP, RJ, MG, RS, PR, SC, BA, GO, DF.
Demais estados usam média nacional como estimativa.

Para atualizar os preços: baixe o XLSX mensal gratuito em [caixa.gov.br › SINAPI](https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/) e substitua os valores em `sinapi_client.py`.

---

## Instalação local

### 1. Clone o repositório

```bash
git clone https://github.com/renata-rocha-create/M7T2_ATIVIDADE.git
cd M7T2_ATIVIDADE/QuantAI
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

> **Nota sobre ifcopenshell:** se o pip não encontrar o pacote, use:
> ```bash
> pip install ifcopenshell --extra-index-url https://s3.amazonaws.com/ifcopenshell-builds/
> ```
> Ou baixe o wheel compatível com seu Python em [ifcopenshell.org/python](https://ifcopenshell.org/python/).

### 4. Execute o app

```bash
streamlit run app.py
```

O app abre automaticamente em `http://localhost:8501`.

---

## Deploy no Streamlit Cloud

O app está configurado para deploy no [Streamlit Community Cloud](https://share.streamlit.io):

| Campo | Valor |
|---|---|
| Repository | `renata-rocha-create/M7T2_ATIVIDADE` |
| Branch | `main` |
| Main file path | `QuantAI/app.py` |
| Python version | `3.11` |

---

## Referências normativas

| Referência | Uso |
|---|---|
| **SINAPI / CEF** | Unidades de medida e critérios de medição — referência nacional |
| **TCPO — PINI** | Critérios de desconto de vãos e arredondamentos |
| **NBR 12721** | Avaliação de custos unitários — áreas computáveis e não computáveis |
| **ISO 19650** | Organização da informação BIM — nomenclatura IFC |
| **ifcopenshell.org** | Biblioteca Python para leitura de arquivos IFC |

---

## Dependências

```
streamlit>=1.35.0
ifcopenshell>=0.7.0
plotly>=5.22.0
openpyxl>=3.1.0
requests>=2.31.0
pandas>=2.0.0
```

---

*Projeto acadêmico — Master IA para AEC · Zigurat Institute of Technology · 2026*
