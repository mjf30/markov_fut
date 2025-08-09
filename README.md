# TCC — Cadeias de Markov em Futebol (StatsBomb Open Data)

Projeto **simples e científico** para modelar partidas de futebol com **Cadeias de Markov de 1ª ordem** usando **StatsBomb Open Data** (eventos).  
O foco é **clareza**, **legibilidade** e **reprodutibilidade** — em poucos arquivos fáceis de alterar.

> **Atribuição obrigatória**: *Data source: StatsBomb Open Data (academic, non-commercial use).*

## Estrutura
```
tcc-markov/
├─ README.md
├─ requirements.txt
├─ config.yaml
├─ run.py
├─ src/
│  ├─ markov_futebol.py
│  └─ plotting.py
└─ data/
   ├─ raw/          # JSONs do Open Data (ou cache do statsbombpy)
   ├─ interim/      # eventos limpos + campos auxiliares
   └─ outputs/      # modelos, figuras e tabelas finais
```

## Como obter os dados
Este projeto utiliza o [StatsBomb Open Data](https://github.com/statsbomb/open-data).

1. **Clone o repositório oficial:**
   ```bash
   git clone https://github.com/statsbomb/open-data.git _open_data_repo
   ```

2. **Copie os dados para a pasta `data/raw`:**
   ```bash
   mkdir -p data/raw
   cp -r _open_data_repo/data/* data/raw/
   ```

## Como rodar o pipeline completo
Para garantir a reprodutibilidade, siga os passos:

1. **Crie um ambiente virtual e instale as dependências:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Execute o pipeline completo:**
   O comando a seguir executa todas as etapas, desde a limpeza dos dados até a geração de métricas e figuras.
   ```bash
   python run.py --all --config config.yaml
   ```

   As etapas individuais (`--clean`, `--states`, `--edges`, `--estimate`, `--evaluate`, `--figures`) também podem ser executadas separadamente.

## Modelo (resumo)
- **Estado = (role, zone, action)**  
  `role ∈ {"atk","def"}`; `zone` = grid 3×3 (x:[0,40)[40,80)[80,120]; y:[0,26.66)[26.66,53.33)[53.33,80]);  
  `action ∈ {"pass","carry","dribble","shot","clearance","other"}`.
- **Orientação**: padronize coordenadas para a **perspectiva do time em posse**:  
  eventos do time **sem posse** → espelhar `(sx,sy)=(120-x, 80-y)`.
- **Transições**: “intra” (mesmo time) e “flip” (troca de posse).  
  Causas (heurística): `interception > tackle > foul_won > out > miscontrol > pressure_loss > other`.
- **Estimativa**: contagens \(C\) → suavização (α=0.3) → normalização por linha → \(P\) + blocos \(A,B,C,D\).
- **Padrões**: *Ball Receipt* não gera arestas; `shot` terminal (padrão).

## Saídas
- `data/outputs/models/`: `P_full.npz`, `P_blocks.npz`, `state_index.json`
- `data/outputs/figures/`: `heatmap_recovery.png`, `graph_threshold.png`, `sankey_kernel.png`
- `data/outputs/tables/`: `metrics.csv`, `recovery_rates.csv`, `kernel_flip.csv`
# markov_fut
# markov_fut
# markov_fut
# markov_fut
# markov_fut
# markov_fut
# markov_fut
