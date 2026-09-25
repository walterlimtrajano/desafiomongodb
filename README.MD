# 🎯 GeoLog — Plataforma de Telemetria Logística e Persistência Poliglota

Desafio Integrador — Laboratório Prático de **Implementação e Gerenciamento de Bancos de Dados NoSQL** (UNIPÊ).

Aplicação Streamlit que demonstra o padrão de **Persistência Poliglota**, combinando:
- **SQLite** — dados transacionais e cadastrais (motoristas e veículos), com integridade referencial.
- **MongoDB** — dados de telemetria/IoT (GPS, temperatura, velocidade), com índice geoespacial `2dsphere` e busca por proximidade (`$near`).

O dashboard une as duas fontes em memória e exibe mapa interativo (Folium), KPIs e gráficos analíticos (Plotly).

## 👥 Equipe e contribuições

| Integrante | Contribuição |
|---|---|
| Walterlim Trajano da Silva Júnior | Desenvolvimento do código (`app.py`) e banco de dados |
| Lucas Holanda | Elaboração do diagrama de arquitetura |
| Daniel Leite Silveira Palitó | Elaboração do PDF do relatório técnico |

## 🏗️ Arquitetura

O diagrama completo está no relatório técnico (`Relatorio_Tecnico_GeoLog.pdf`), incluído neste repositório.

```
Usuário/Gestor Logístico
        │
        ▼
Plataforma GeoLog (Streamlit)
   ├── Módulo 1: Seed & Conexões (sqlite3 / pymongo)
   ├── Módulo 2: Geoprocessamento & Raio (Folium / $near)
   ├── Módulo 3: Join Poliglota (combinação em memória)
   ├── Módulo 4: Dashboard KPIs (Plotly / DataFrames)
   └── Bônus: Simulador de Telemetria IoT em tempo real
        │                              │
        ▼                              ▼
  SQLite (logitech.db)          MongoDB (geolog_db)
  Persistência Relacional       Persistência NoSQL
```

## 📋 Pré-requisitos

- Python 3.10+
- MongoDB rodando localmente em `mongodb://localhost:27017/` (Community Server ou Docker)

## 🚀 Como rodar

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd desafiomongodb

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Garanta que o MongoDB está em execução localmente

# 5. Rode a aplicação (sempre via streamlit, nunca com "python app.py")
streamlit run app.py
```

O app abre automaticamente no navegador em `http://localhost:8501`. Na primeira execução, as tabelas do SQLite e a coleção do MongoDB são criadas e populadas com dados de exemplo (seed).

## 📂 Estrutura do repositório

```
.
├── app.py                          # Aplicação Streamlit (código principal)
├── logitech.db                     # Banco SQLite (gerado/populado no 1º run)
├── requirements.txt                # Dependências Python
├── .gitignore
├── README.md
├── Relatorio_Tecnico_GeoLog.pdf    # Relatório técnico com diagrama de arquitetura
└── Arquitetura_Poliglota_drawio.pdf # Diagrama de arquitetura (fonte)
```

## 🧩 Módulos

1. **Persistência & Seed** — cria e popula `motoristas`, `veiculos` (SQLite) e `telemetria` (MongoDB).
2. **Geoprocessamento & Raio** — busca geoespacial por proximidade (`$near`) com mapa Folium.
3. **Join Poliglota** — combinação em memória entre dados cadastrais e telemetria mais recente.
4. **Dashboard Analítico** — KPIs e gráficos Plotly (status dos motoristas, histórico de temperatura).
5. **Bônus** — simulador de movimentação que gera novos pontos GPS em tempo real.

## 📄 Entregáveis

- [x] Código-fonte (`app.py`)
- [x] Banco SQLite (`logitech.db`)
- [x] Relatório técnico em PDF com diagrama de arquitetura poliglota