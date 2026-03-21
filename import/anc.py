import pandas as pd
from datasets import Dataset, DatasetDict
from huggingface_hub import hf_hub_download
from huggingface_hub import login

login()  # enter your token

# Download the parquet file directly
parquet_path = hf_hub_download(
    repo_id="h4ng/necai",
    filename="openings/train-00000-of-00001.parquet",
    repo_type="dataset"
)

# Read it with pandas directly
df = pd.read_parquet(parquet_path)

print(df.columns.tolist())  # verify columns
print(len(df))              # verify row count

# Add the percentage column
df["percentage"] = None

# Convert back to Dataset and push
dataset = Dataset.from_pandas(df)

dataset.push_to_hub("h4ng/necai", config_name="openings", split="train")

print("Done! Columns:", dataset.column_names)