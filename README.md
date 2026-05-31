# M7T2_ATIVIDADE
 QuantAI — Quantificação Arquitetônica BIM

**M7T2 · Zigurat Institute of Technology · Prof. Thomas Takeuchi · Aluna: Renata Rocha**

App Streamlit para extração de quantitativos de arquitetura a partir de arquivos IFC,
com preços SINAPI em tempo real via API do Orçamentador.

---

## Estrutura do projeto

```
quantai_app/
├── app.py              # App Streamlit principal
├── extrator_ifc.py     # Extração de quantitativos com IfcOpenShell
├── sinapi_client.py    # Integração com a API SINAPI do Orçamentador
├── excel_export.py     # Geração do Excel em memória (3 abas)
├── requirements.txt    # Dependências Python
└── README.md
```

---

## Instalação

### 1. Crie um ambiente virtual (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

> **Nota sobre ifcopenshell**: em alguns ambientes o pip não encontra
> o pacote diretamente. Nesse caso, use:
> ```bash
> pip install ifcopenshell --extra-index-url https://s3.amazonaws.com/ifcopenshell-builds/
> ```
> Ou baixe o wheel compatível com seu Python em [ifcopenshell.org/python](https://ifcopenshell.org/python/).

### 3. Obtenha a API Key SINAPI (gratuita)

Cadastre-se em [orcamentador.com.br/api](https://orcamentador.com.br/api)
e solicite a chave de acesso gratuita.

---

## Execução

```bash
streamlit run app.py
```

O app abre automaticamente em `http://localhost:8501`.

---

## Fluxo de uso

1. Configure a **API Key SINAPI** na barra lateral
2. Selecione o **estado** e o **regime de preços** (desonerado / não desonerado)
3. Marque o **escopo** de extração desejado
4. Faça upload do arquivo **.ifc** (IFC 2x3 ou IFC 4)
5. Clique em **Processar IFC**
6. Explore as abas: Quantitativos · Gráfico por categoria · Mapa de calor · Exportar Excel

---

## Entidades IFC mapeadas

| Entidade IFC         | PredefinedType              | Elemento extraído                     |
|----------------------|-----------------------------|---------------------------------------|
| `IfcCovering`        | FLOORING                    | Revestimento cerâmico — piso          |
| `IfcCovering`        | CLADDING                    | Revestimento cerâmico — parede        |
| `IfcCovering`        | CEILING                     | Forro de gesso acartonado             |
| `IfcCovering`        | BASEBOARD                   | Rodapé cerâmico                       |
| `IfcDoor`            | —                           | Porta de madeira completa             |
| `IfcWindow`          | —                           | Janela de alumínio — correr           |
| `IfcSanitaryTerminal`| WC / SINK / SHOWER / BATH   | Louças e metais sanitários            |
| `IfcSlab`            | ROOF                        | Impermeabilização — manta asfáltica   |

---

## API SINAPI — Orçamentador

- Documentação: [orcamentador.com.br/api/docs](https://orcamentador.com.br/api/docs)
- Endpoint usado: `GET /orcamento/` — envia todos os códigos + quantidades em lote
- Formato dos itens: `C:87549@412.50,C:87285@188.30,...`
  - `C:` = composição SINAPI (serviço com mão de obra embutida)
- Parâmetros: `apikey`, `estado`, `regime` (desonerado / nao_desonerado)

---

## Referências normativas

- **SINAPI / CEF** — critérios de medição e preços de referência
- **TCPO — PINI** — desconto de vãos e arredondamentos
- **NBR 12721** — áreas computáveis e não computáveis
- **ISO 19650** — nomenclatura IFC e BIM

