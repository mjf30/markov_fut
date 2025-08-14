# markov-futebol

Projeto simples para **modelar transições táticas** em partidas de futebol usando **Cadeias de Markov de primeira ordem**, a partir do repositório **StatsBomb Open Data** (incluído neste projeto).

> Estados = (posse, zona, ação, situação do jogo)

- **Posse**: `P` (com posse) — derivado de `possession_team`.
- **Zona** (eixo X do campo): `D` (0–40), `M` (40–80), `A` (80–120).
- **Ação** (mapeamento discreto): `PAS` (passa), `FIN` (finaliza), `PER` (perde), `REC` (recupera).
- **Situação**: `FAV` (placar favorável), `NEU` (empate), `DES` (desfavorável).

O pipeline varre eventos, **extrai sequências por posse** e **conta transições sucessivas** da mesma equipe. Em seguida normaliza para formar a **matriz de transição** e gera um **grafo dirigido** das transições dominantes.

O caminho dos dados (`--data-root`) aponta por padrão para a pasta local `./_open_data_repo`.

## Instalação rápida (modo dev)

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -e .
```

## Uso

Existem dois modos principais: `build` (com IDs numéricos) e `run` (com nomes em um arquivo de configuração).

### 1. Comando `build` (com IDs)

Exemplo: Premier League 2017/2018 (IDs fictícios).

```bash
markov-futebol build --out ./saida --competition 2 --season 1
```

Isso cria:
- `saida/transition_counts.csv` (contagens)
- `saida/transition_matrix.csv` (probabilidades)
- `saida/states.csv` (dicionário de estados observados)
- `saida/graph.png` (grafo das transições mais prováveis)

Você também pode rodar em **um jogo específico**:
```bash
markov-futebol build --out ./saida_jogo --match-id 303471
```

### 2. Comando `run` (com `config.yaml`)

1) Copie `config.example.yaml` para `config.yaml`.
2) Edite os nomes da competição, temporada e (opcional) time. O campo `data_root` é opcional.

3) Rode:
```bash
markov-futebol run config.yaml
```

O script resolve os IDs automaticamente e executa o pipeline.

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
