# Play And Learn

This folder generates memoization data by having NECAI play against Stockfish in many games at once.

Each recorded row stores:

- `fen`: board state before NECAI moves
- `current_move`: NECAI's move in UCI
- `next_move`: Stockfish's reply in UCI
- `next_fen`: board state after Stockfish's reply
- `color`: whether NECAI was white or black in that game
- `percentage`: always starts at `100.0`
- `game_id`, `ply`, `game_result`, `termination`

## Run

From the repo root:

```bash
./venv/bin/python playandlearn/generate-games.py \
  --games-per-color 25 \
  --max-workers 25
```

By default, the script uses the local binary at `playandlearn/stockfish`.
You only need `--stockfish-path` if you want to override it.

This writes local files to:

- `necai/memoization/white/train.jsonl`
- `necai/memoization/white/train-00000-of-00001.parquet`
- `necai/memoization/black/train.jsonl`
- `necai/memoization/black/train-00000-of-00001.parquet`

## Start From Memoization FENs

To start each game from a random FEN already present in your local memoization subsets:

```bash
./venv/bin/python playandlearn/generate-games-from-memoization.py \
  --games-per-color 25 \
  --max-workers 25
```

By default, this script reads from:

- `necai/memoization/white/train-00000-of-00001.parquet`
- `necai/memoization/black/train-00000-of-00001.parquet`

and writes the generated rows back to:

- `necai/memoization/white/train.jsonl`
- `necai/memoization/white/train-00000-of-00001.parquet`
- `necai/memoization/black/train.jsonl`
- `necai/memoization/black/train-00000-of-00001.parquet`

## Start From Random Legal FENs

To generate genuinely random but legal starting positions, then continue the
games against Stockfish:

```bash
./venv/bin/python playandlearn/generate-games-from-random-fens.py \
  --games-per-color 25 \
  --max-workers 25
```

This script creates each starting FEN by playing a random sequence of legal
moves from the standard initial position, while making sure the final board is
still legal and that it is NECAI's turn.

Useful knobs:

- `--min-random-plies 6`
- `--max-random-plies 24`
- `--stockfish-depth 8`
- `--push-to-hub`

## Push To Hugging Face

If you want the script to upload directly into your existing subsets:

```bash
./venv/bin/python playandlearn/generate-games.py \
  --games-per-color 25 \
  --max-workers 25 \
  --push-to-hub
```

It pushes to:

- `h4ng/necai` / `memoization_white`
- `h4ng/necai` / `memoization_black`
