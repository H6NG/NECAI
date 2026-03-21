
#Thanks to Lichess Oauth Token

import pandas as pd
import requests
import chess
import chess.pgn
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from datasets import Dataset, Features, Value
from huggingface_hub import hf_hub_download, login

# ── Config ──────────────────────────────────────────────
LICHESS_TOKEN = "lip_xxxxxxxxxxxxxxxx"  # paste your token here 
HF_REPO = "h4ng/necai"
MAX_WORKERS = 10  # 10 parallel requests at once
# ────────────────────────────────────────────────────────

login()

parquet_path = hf_hub_download(
    repo_id=HF_REPO,
    filename="openings/train-00000-of-00001.parquet",
    repo_type="dataset"
)

df = pd.read_parquet(parquet_path)

def pgn_to_uci(pgn_string):
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        return ",".join(move.uci() for move in game.mainline_moves())
    except:
        return ""

def get_win_rate(index, pgn_moves, name):
    try:
        uci = pgn_to_uci(pgn_moves)
        if not uci:
            return index, None

        r = requests.get(
            "https://explorer.lichess.ovh/lichess",
            headers={"Authorization": f"Bearer {LICHESS_TOKEN}"},
            params={
                "play": uci,
                "moves": 0,
                "topGames": 0,
                "recentGames": 0,
                "ratings": "2000,2200,2500",
            },
            timeout=10
        )

        if r.status_code != 200:
            return index, None

        data = r.json()
        total = data.get("white", 0) + data.get("draws", 0) + data.get("black", 0)
        if total == 0:
            return index, None

        rate = round(data["white"] / total * 100, 2)
        print(f"[{index+1}/{len(df)}] {name[:45]} → {rate}%")
        return index, rate

    except Exception as e:
        print(f"[{index+1}] Error: {e}")
        return index, None

# Run in parallel
percentages = [None] * len(df)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(get_win_rate, i, row["pgn"], row["name"]): i
        for i, row in df.iterrows()
    }
    for future in as_completed(futures):
        index, rate = future.result()
        percentages[index] = rate

df["percentage"] = percentages

# Push to Hugging Face
features = Features({
    "eco":        Value("large_string"),
    "name":       Value("large_string"),
    "pgn":        Value("large_string"),
    "fen":        Value("large_string"),
    "percentage": Value("float64"),
})

dataset = Dataset.from_pandas(df, features=features)
dataset.push_to_hub(HF_REPO, config_name="openings", split="train")

print("\n✅ Done!")
print(df[["name", "percentage"]].dropna().head(10))