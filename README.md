# markov-futebol

Projeto simples para **modelar transições táticas** em partidas de futebol usando **Cadeias de Markov de primeira ordem**, a partir do repositório **StatsBomb Open Data** (incluído neste projeto).

> Estados = (posse, zona, ação, situação do jogo)

- **Posse**: `P` (com posse) — derivado de `possession_team`.
- **Zona** (eixo X do campo): `D` (0–40), `M` (40–80), `A` (80–120).
- **Ação** (mapeamento discreto): `PAS` (passa), `FIN` (finaliza), `PER` (perde), `REC` (recupera).
- **Situação**: `FAV` (placar favorável), `NEU` (empate), `DES` (desfavorável).

O pipeline varre eventos, **extrai sequências por posse** e **conta transições sucessivas** da mesma equipe. Em seguida normaliza para formar a **matriz de transição** e gera um **grafo dirigido** das transições dominantes.

## Instalação rápida (modo dev)

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -e .
```

## Uso

Toda a configuração é feita através de um arquivo `config.yaml`.

1) Edite `config.yaml` para definir o escopo da análise (usando nomes ou IDs) e outros parâmetros.

Exemplo de `config.yaml`:
```yaml
# Raiz do repositório open-data (opcional, default: ./_open_data_repo)
data_root: ./statsbomb_data

# Pasta de saída (opcional, default: ./saida)
out: ./saida

# --- MODO DE EXECUÇÃO ---
# Escolha UMA das seções abaixo: 'scope' (nomes) ou 'ids' (números).
# Se ambas estiverem preenchidas, 'ids' terá prioridade.

# Seção 1: Usar nomes (mais fácil)
scope:
  competition: "La Liga"
  season: "2020/2021"
  # team: "Barcelona"  # Opcional: filtrar por um time específico

# Seção 2: Usar IDs numéricos
ids:
  competition_id: null
  season_id: null
  # match_id: 3788872 # Opcional: para rodar em um único jogo

# --- PARÂMETROS DE ANÁLISE ---
params:
  # Incluir a situação do jogo (placar) na análise? (true/false)
  incluir_situacao: true
  # Arestas com probabilidade mínima para o grafo (0.0 a 1.0)
  prob_threshold: 0.05
```

2) Rode o comando:
```bash
markov-soccer run config.yaml
```

O script irá gerar os seguintes arquivos na pasta de saída definida:
- `transition_counts.csv` (contagens)
- `transition_matrix.csv` (probabilidades)
- `states.csv` (dicionário de estados observados)
- `graph.png` (grafo das transições mais prováveis)

## Decisões e ajustes em relação ao pré‑projeto

- **Estados discretos**: mantivemos quatro dimensões propostas; para zona, usamos apenas o eixo **X** (0–120) dividido em três terços iguais.  
- **Ações**: reduzimos para {`PAS`, `FIN`, `PER`, `REC`} como no pré-projeto. Passes incompletos e perdas de bola (`Dispossessed`, `Miscontrol`) viram **PER**; `Ball Recovery` vira **REC**.
- **Posse**: só consideramos eventos em que `team` == `possession_team` de cada evento (transições “válidas” da mesma equipe).
- **Placar em tempo real**: o script reconstrói o placar **percorrendo os eventos** e detectando gols em `shot.outcome == "Goal"` (ou `own_goal`). Situação do jogo é calculada **relativa à equipe do evento**.
- **Sequências por posse**: eventos são **segmentados pelo campo `possession`**; cada sequência contribui com transições `sᵢ → sⱼ`.
- **Campos sem localização**: eventos sem `location` são ignorados para transições.
- **Visualização**: geramos um grafo dirigindo **apenas arestas com probabilidade ≥ 0.05** para deixar a figura legível.

## Limitações conhecidas
- Mapeamento de ações é propositalmente **simples**.
- Nem todos os eventos têm `location`.
- As regras de posse dos dados StatsBomb são respeitadas, mas o projeto mantém a **primeira ordem** da cadeia.

## Licença
Projeto acadêmico para estudo. Dados por StatsBomb Open Data (créditos dos dados no repositório oficial).