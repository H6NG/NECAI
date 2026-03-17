# NECAI
**Neural Engine for Chess AI**

A chess engine powered by machine learning, trained on 
billions of positions from various databases combined into one. 

## Overview
NECAI is a chess AI built from scratch using neural networks
and classical search algorithms. The goal is to build a 
strong, self-improving chess engine using modern ML techniques
inspired by AlphaZero and Leela Chess Zero.

## Architecture
- **Engine** — Core chess logic written in C++/Python
- **Neural Network** — Position evaluation model (PyTorch)
- **Dataset** — 2000+ Elo rated games from Lichess (CC0)
- **Search** — Alpha-Beta / MCTS algorithm

## Dataset
- Source: [Collection of Datasets](https://huggingface.co/datasets/h4ng/necai/tree/main)
- Format: FEN positions stored as Parquet files
- Hosted on: [Hugging Face](https://huggingface.co/datasets/h4ng/necai/tree/main)
- Filter: Both players rated 2000+, complete games only

## Project Structure

```
NECAI/
├── engine/        # Core chess engine (C++/Python)
├── test/          # CI/CD tests
├── .gitignore
└── README.md
```

## Stack
| Layer | Tool |
|-------|------|
| Language | Python / C++ |
| ML Framework | PyTorch |
| Chess Library | ??? |
| Database | Hugging Face |
| Dataset hosting | Hugging Face |
| CI/CD | GitHub Actions |

## Status
🚧 Work in progress

## License
MIT