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
OUTPUT_DIR = PROJECT_ROOT / "necai" / "memoization"
DEFAULT_REPO_ID = "h4ng/necai"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate memoization rows by starting from random legal FENs, "
            "then letting NECAI play against Stockfish."
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
        "--min-random-plies",
        type=int,
        default=6,
        help="Minimum random plies used to create a legal starting FEN.",
    )
    parser.add_argument(
        "--max-random-plies",
        type=int,
        default=24,
        help="Maximum random plies used to create a legal starting FEN.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used when creating starting FENs.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where white/black memoization files will be written.",
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


def legal_start_ply_choices(color: str, min_random_plies: int, max_random_plies: int) -> list[int]:
    expected_parity = 0 if color == "white" else 1
    choices = [
        ply
        for ply in range(min_random_plies, max_random_plies + 1)
        if ply % 2 == expected_parity
    ]
    if not choices:
        raise ValueError(
            f"No ply counts in range [{min_random_plies}, {max_random_plies}] match color={color}"
        )
    return choices


def generate_random_legal_fen(
    color: str,
    rng: random.Random,
    min_random_plies: int,
    max_random_plies: int,
    max_attempts: int = 200,
) -> str:
    target_choices = legal_start_ply_choices(color, min_random_plies, max_random_plies)
    expected_turn = chess.WHITE if color == "white" else chess.BLACK

    for _ in range(max_attempts):
        board = chess.Board()
        target_plies = rng.choice(target_choices)

        while board.ply() < target_plies and not board.is_game_over(claim_draw=True):
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                break
            board.push(rng.choice(legal_moves))

        if board.turn != expected_turn:
            continue
        if board.is_game_over(claim_draw=True):
            continue
        if not board.is_valid():
            continue

        return board.fen()

    raise RuntimeError(f"Could not generate a random legal FEN for color={color}")


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
    game_id = f"{color}-random-{game_index + 1:04d}"
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

    new_df = pd.DataFrame(rows)
    parquet_path = color_dir / "train-00000-of-00001.parquet"
    jsonl_path = color_dir / "train.jsonl"

    if parquet_path.exists():
        existing_df = pd.read_parquet(parquet_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    combined_df.to_json(jsonl_path, orient="records", lines=True)
    combined_df.to_parquet(parquet_path, index=False)
    return parquet_path


def push_rows(rows: list[dict], repo_id: str, subset_name: str) -> None:
    dataset = Dataset.from_list(rows, features=dataset_features())
    dataset.push_to_hub(repo_id, config_name=subset_name, split="train")


def main() -> None:
    args = parse_args()

    stockfish_path = Path(args.stockfish_path).expanduser().resolve()
    necai_engine_path = Path(args.necai_engine_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not stockfish_path.exists():
        raise FileNotFoundError(f"Stockfish binary not found: {stockfish_path}")
    if not necai_engine_path.exists():
        raise FileNotFoundError(f"NECAI engine binary not found: {necai_engine_path}")

    print_lock = threading.Lock()
    tasks = []
    all_rows = {"white": [], "black": []}
    master_rng = random.Random(args.seed)

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for color in ("white", "black"):
            for game_index in range(args.games_per_color):
                start_seed = master_rng.randint(0, 10**9)
                start_fen = generate_random_legal_fen(
                    color=color,
                    rng=random.Random(start_seed),
                    min_random_plies=args.min_random_plies,
                    max_random_plies=args.max_random_plies,
                )
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
        print(f"Saved {len(rows)} new rows into {parquet_path}")

        if args.push_to_hub:
            print(f"Pushing {subset_name} to {args.repo_id}")
            push_rows(rows, args.repo_id, subset_name)


if __name__ == "__main__":
    main()
