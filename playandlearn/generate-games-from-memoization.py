import argparse
import json
import random
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import chess
import chess.engine
import pandas as pd
from datasets import Dataset, Features, Value


PROJECT_ROOT = Path(__file__).resolve().parent.parent
NECAI_ENGINE_PATH = PROJECT_ROOT / "engine" / "cpp" / "necai_engine"
STOCKFISH_PATH = PROJECT_ROOT / "playandlearn" / "stockfish"
MEMOIZATION_DIR = PROJECT_ROOT / "necai" / "memoization"
DEFAULT_REPO_ID = "h4ng/necai"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate memoization rows by starting games from random FENs "
            "sampled from the local memoization subsets."
        )
    )
    parser.add_argument(
        "--stockfish-path",
        default=str(STOCKFISH_PATH),
        help="Path to the Stockfish binary.",
    )
    parser.add_argument(
        "--necai-engine-path",
        default=str(NECAI_ENGINE_PATH),
        help="Path to the compiled NECAI engine binary.",
    )
    parser.add_argument(
        "--source-dir",
        default=str(MEMOIZATION_DIR),
        help="Directory containing memoization/white and memoization/black parquet files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(MEMOIZATION_DIR),
        help="Directory where generated white/black memoization files will be written.",
    )
    parser.add_argument(
        "--games-per-color",
        type=int,
        default=25,
        help="How many games to run as white and as black.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=25,
        help="How many games to play concurrently.",
    )
    parser.add_argument(
        "--necai-depth",
        type=int,
        default=1,
        help="Search depth used for the NECAI engine.",
    )
    parser.add_argument(
        "--stockfish-depth",
        type=int,
        default=8,
        help="Search depth used for Stockfish.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=200,
        help="Safety cap on total half-moves per game.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used when sampling starting FENs.",
    )
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help="Hugging Face dataset repo id.",
    )
    parser.add_argument(
        "--push-to-hub",
        action="store_true",
        help="Push generated rows to Hugging Face after local export.",
    )
    return parser.parse_args()


def dataset_features() -> Features:
    return Features(
        {
            "game_id": Value("string"),
            "color": Value("string"),
            "ply": Value("int64"),
            "fen": Value("large_string"),
            "current_move": Value("string"),
            "next_move": Value("string"),
            "next_fen": Value("large_string"),
            "percentage": Value("float64"),
            "game_result": Value("string"),
            "termination": Value("string"),
        }
    )


def run_necai_move(fen: str, depth: int, engine_path: Path) -> dict:
    result = subprocess.run(
        [str(engine_path), fen, str(depth)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip())


def play_stockfish_move(board: chess.Board, engine: chess.engine.SimpleEngine, depth: int) -> str:
    result = engine.play(board, chess.engine.Limit(depth=depth))
    if result.move is None:
        raise RuntimeError("Stockfish returned no move")

    move_uci = result.move.uci()
    board.push(result.move)
    return move_uci


def summarize_result(board: chess.Board, max_plies_hit: bool) -> tuple[str, str]:
    if max_plies_hit:
        return "*", "max_plies"

    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        return "*", "unfinished"

    if outcome.winner is True:
        result = "1-0"
    elif outcome.winner is False:
        result = "0-1"
    else:
        result = "1/2-1/2"

    return result, outcome.termination.name.lower()


def load_fen_pool(source_dir: Path, color: str) -> list[str]:
    parquet_path = source_dir / color / "train-00000-of-00001.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Memoization subset not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    if "fen" not in df.columns:
        raise ValueError(f"Expected 'fen' column in {parquet_path}, found {list(df.columns)}")

    fens = []
    for fen in df["fen"].dropna().tolist():
        try:
            board = chess.Board(fen)
        except ValueError:
            continue
        expected_turn = chess.WHITE if color == "white" else chess.BLACK
        if board.turn == expected_turn and not board.is_game_over(claim_draw=True):
            fens.append(fen)

    if not fens:
        raise ValueError(f"No usable {color} FENs found in {parquet_path}")

    return fens


def play_single_game(
    color: str,
    game_index: int,
    start_fen: str,
    stockfish_path: Path,
    necai_engine_path: Path,
    necai_depth: int,
    stockfish_depth: int,
    max_plies: int,
    print_lock: threading.Lock,
) -> list[dict]:
    board = chess.Board(start_fen)
    rows: list[dict] = []
    max_plies_hit = False
    game_id = f"{color}-memo-{game_index + 1:04d}"
    bot_is_white = color == "white"

    with chess.engine.SimpleEngine.popen_uci(str(stockfish_path)) as stockfish:
        while not board.is_game_over(claim_draw=True):
            if board.ply() >= max_plies:
                max_plies_hit = True
                break

            if board.turn != bot_is_white:
                play_stockfish_move(board, stockfish, stockfish_depth)
                continue

            fen_before = board.fen()
            engine_data = run_necai_move(fen_before, necai_depth, necai_engine_path)
            if engine_data.get("game_over"):
                break

            current_move = engine_data.get("best_move")
            if not current_move:
                raise RuntimeError(f"NECAI returned no move for {game_id}")

            bot_move = chess.Move.from_uci(current_move)
            if bot_move not in board.legal_moves:
                raise RuntimeError(f"Illegal NECAI move for {game_id}: {current_move}")

            board.push(bot_move)

            next_move = ""
            next_fen = board.fen()

            if not board.is_game_over(claim_draw=True):
                next_move = play_stockfish_move(board, stockfish, stockfish_depth)
                next_fen = board.fen()

            rows.append(
                {
                    "game_id": game_id,
                    "color": color,
                    "ply": len(rows) + 1,
                    "fen": fen_before,
                    "current_move": current_move,
                    "next_move": next_move,
                    "next_fen": next_fen,
                    "percentage": 100.0,
                    "game_result": "*",
                    "termination": "",
                }
            )

    result, termination = summarize_result(board, max_plies_hit)
    for row in rows:
        row["game_result"] = result
        row["termination"] = termination

    with print_lock:
        print(
            f"[{game_id}] start_fen={start_fen[:30]}... rows={len(rows)} "
            f"result={result} termination={termination}"
        )

    return rows


def export_rows(rows: list[dict], output_dir: Path, color: str) -> Path:
    color_dir = output_dir / color
    color_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)

    jsonl_path = color_dir / "train.jsonl"
    parquet_path = color_dir / "train-00000-of-00001.parquet"

    df.to_json(jsonl_path, orient="records", lines=True)
    df.to_parquet(parquet_path, index=False)
    return parquet_path


def push_rows(rows: list[dict], repo_id: str, subset_name: str) -> None:
    dataset = Dataset.from_list(rows, features=dataset_features())
    dataset.push_to_hub(repo_id, config_name=subset_name, split="train")


def main() -> None:
    args = parse_args()

    stockfish_path = Path(args.stockfish_path).expanduser().resolve()
    necai_engine_path = Path(args.necai_engine_path).expanduser().resolve()
    source_dir = Path(args.source_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not stockfish_path.exists():
        raise FileNotFoundError(f"Stockfish binary not found: {stockfish_path}")
    if not necai_engine_path.exists():
        raise FileNotFoundError(f"NECAI engine binary not found: {necai_engine_path}")

    random.seed(args.seed)
    fen_pools = {
        "white": load_fen_pool(source_dir, "white"),
        "black": load_fen_pool(source_dir, "black"),
    }

    print_lock = threading.Lock()
    tasks = []
    all_rows = {"white": [], "black": []}

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for color in ("white", "black"):
            for game_index in range(args.games_per_color):
                start_fen = random.choice(fen_pools[color])
                tasks.append(
                    executor.submit(
                        play_single_game,
                        color,
                        game_index,
                        start_fen,
                        stockfish_path,
                        necai_engine_path,
                        args.necai_depth,
                        args.stockfish_depth,
                        args.max_plies,
                        print_lock,
                    )
                )

        for future in as_completed(tasks):
            rows = future.result()
            if rows:
                all_rows[rows[0]["color"]].extend(rows)

    subset_map = {
        "white": "memoization_white",
        "black": "memoization_black",
    }

    for color, subset_name in subset_map.items():
        rows = all_rows[color]
        if not rows:
            print(f"No rows generated for {subset_name}")
            continue

        parquet_path = export_rows(rows, output_dir, color)
        print(f"Saved {len(rows)} rows to {parquet_path}")

        if args.push_to_hub:
            print(f"Pushing {subset_name} to {args.repo_id}")
            push_rows(rows, args.repo_id, subset_name)


if __name__ == "__main__":
    main()
