import { useState } from "react"
import { Chess } from "chess.js"

const files = ["a", "b", "c", "d", "e", "f", "g", "h"]

function getBoardFromFen(chess) {
  const board = Array.from({ length: 8 }, () => Array(8).fill(null))
  const position = chess.board()

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const piece = position[row][col]
      if (piece) {
        board[row][col] = piece.color + piece.type.toUpperCase()
      }
    }
  }

  return board
}

function toSquare(row, col) {
  return files[col] + (8 - row)
}

export default function App() {
  const [chess, setChess] = useState(new Chess())
  const [board, setBoard] = useState(getBoardFromFen(new Chess()))
  const [draggedFrom, setDraggedFrom] = useState(null)
  const [legalTargets, setLegalTargets] = useState([])
  const [status, setStatus] = useState("Your move")
  const [isThinking, setIsThinking] = useState(false)
  const [lastSource, setLastSource] = useState(null)
  const [engineEval, setEngineEval] = useState(null)
  const [modelEval, setModelEval] = useState(null)
  const [lastBotMove, setLastBotMove] = useState(null)
  const [playerColor, setPlayerColor] = useState("white")

  const botColor = playerColor === "white" ? "black" : "white"

  const displayRows =
    playerColor === "white"
      ? [0, 1, 2, 3, 4, 5, 6, 7]
      : [7, 6, 5, 4, 3, 2, 1, 0]

  const displayCols =
    playerColor === "white"
      ? [0, 1, 2, 3, 4, 5, 6, 7]
      : [7, 6, 5, 4, 3, 2, 1, 0]

  async function requestBotMove(currentChess, currentBotColor) {
    try {
      const response = await fetch("http://localhost:5001/move", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fen: currentChess.fen(),
          pgn_so_far: currentChess.pgn(),
          color: currentBotColor,
        }),
      })

      const data = await response.json()
      console.log("Bot response:", data)
      return data
    } catch (error) {
      console.error("Failed to fetch bot move:", error)
      return null
    }
  }

  async function makeBotMove(currentChess, currentBotColor) {
    setStatus("NECAI is thinking...")
    setIsThinking(true)

    const botData = await requestBotMove(currentChess, currentBotColor)

    if (!botData) {
      setStatus("Failed to reach backend")
      setIsThinking(false)
      return
    }

    if (botData.game_over) {
      setStatus(`Game over: ${botData.reason || "finished"}`)
      setLastSource(botData.source ?? null)
      setEngineEval(botData.engine_eval ?? null)
      setModelEval(botData.model_eval ?? null)
      setIsThinking(false)
      return
    }

    if (!botData.move_uci) {
      setStatus(botData.message || "No move returned")
      setLastSource(botData.source ?? null)
      setEngineEval(botData.engine_eval ?? null)
      setModelEval(botData.model_eval ?? null)
      setIsThinking(false)
      return
    }

    const next = new Chess(currentChess.fen())
    const move = next.move({
      from: botData.move_uci.slice(0, 2),
      to: botData.move_uci.slice(2, 4),
      promotion: botData.move_uci.length === 5 ? botData.move_uci[4] : "q",
    })

    if (!move) {
      setStatus("Backend returned invalid move")
      setIsThinking(false)
      return
    }

    setChess(next)
    setBoard(getBoardFromFen(next))
    setLastBotMove(botData.move || botData.move_uci)
    setLastSource(botData.source ?? null)
    setEngineEval(botData.engine_eval ?? null)
    setModelEval(botData.model_eval ?? null)

    if (next.isCheckmate()) {
      setStatus("Checkmate")
    } else if (next.isStalemate()) {
      setStatus("Stalemate")
    } else if (next.isCheck()) {
      setStatus("Check")
    } else {
      setStatus("Your move")
    }

    setIsThinking(false)
  }

  function handleDragStart(e, row, col) {
    if (isThinking) return
    if (chess.turn() !== playerColor[0]) return

    const from = toSquare(row, col)
    const piece = chess.get(from)

    if (!piece || piece.color !== chess.turn()) return

    e.dataTransfer.setData("text/plain", from)
    e.dataTransfer.effectAllowed = "move"

    const moves = chess.moves({ square: from, verbose: true })
    setDraggedFrom({ row, col })
    setLegalTargets(moves.map((move) => move.to))
  }

  function handleDragOver(e) {
    e.preventDefault()
  }

  async function handleDrop(row, col) {
    if (!draggedFrom || isThinking) return
    if (chess.turn() !== playerColor[0]) return

    const from = toSquare(draggedFrom.row, draggedFrom.col)
    const to = toSquare(row, col)

    const next = new Chess(chess.fen())
    const move = next.move({
      from,
      to,
      promotion: "q",
    })

    setDraggedFrom(null)
    setLegalTargets([])

    if (!move) return

    setChess(next)
    setBoard(getBoardFromFen(next))

    if (next.isCheckmate()) {
      setStatus("Checkmate")
      return
    }

    if (next.isStalemate()) {
      setStatus("Stalemate")
      return
    }

    await makeBotMove(next, botColor)
  }

  function handleDragEnd() {
    setDraggedFrom(null)
    setLegalTargets([])
  }

  function resetBoard(nextPlayerColor = playerColor) {
    const fresh = new Chess()
    setChess(fresh)
    setBoard(getBoardFromFen(fresh))
    setDraggedFrom(null)
    setLegalTargets([])
    setLastSource(null)
    setEngineEval(null)
    setModelEval(null)
    setLastBotMove(null)
    setIsThinking(false)

    if (nextPlayerColor === "black") {
      setStatus("NECAI is thinking...")
      const nextBotColor = "white"
      setTimeout(() => {
        makeBotMove(fresh, nextBotColor)
      }, 100)
    } else {
      setStatus("Your move")
    }
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col items-center justify-center p-6">
      <h1 className="text-white text-3xl font-bold mb-2">NECAI Chess</h1>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => {
            setPlayerColor("white")
            resetBoard("white")
          }}
          className={`px-3 py-2 rounded-lg font-semibold ${
            playerColor === "white"
              ? "bg-white text-black"
              : "bg-neutral-700 text-white"
          }`}
        >
          Play White
        </button>

        <button
          onClick={() => {
            setPlayerColor("black")
            resetBoard("black")
          }}
          className={`px-3 py-2 rounded-lg font-semibold ${
            playerColor === "black"
              ? "bg-white text-black"
              : "bg-neutral-700 text-white"
          }`}
        >
          Play Black
        </button>
      </div>

      <p className="text-neutral-300 mb-1">
        You are: {playerColor === "white" ? "White" : "Black"}
      </p>

      <p className="text-neutral-300 mb-1">
        Turn: {chess.turn() === "w" ? "White" : "Black"}
      </p>

      <p className="text-neutral-400 mb-5">{status}</p>

      <div className="flex flex-col md:flex-row gap-6 items-start">
        <div className="grid grid-cols-8 border-4 border-neutral-700 shadow-2xl">
          {displayRows.flatMap((rowIndex) =>
            displayCols.map((colIndex) => {
              const piece = board[rowIndex][colIndex]
              const isLightSquare = (rowIndex + colIndex) % 2 === 0
              const square = toSquare(rowIndex, colIndex)
              const isLegalTarget = legalTargets.includes(square)

              return (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  onDragOver={handleDragOver}
                  onDrop={() => handleDrop(rowIndex, colIndex)}
                  className={`relative w-14 h-14 flex items-center justify-center ${
                    isLightSquare ? "bg-slate-100" : "bg-blue-700"
                  }`}
                >
                  {isLegalTarget && (
                    <div className="absolute w-4 h-4 rounded-full bg-black/25" />
                  )}

                  {piece && (
                    <img
                      src={`/pieces/${piece}.svg`}
                      alt={piece}
                      draggable={
                        !isThinking &&
                        piece[0] === chess.turn() &&
                        chess.turn() === playerColor[0]
                      }
                      onDragStart={(e) => handleDragStart(e, rowIndex, colIndex)}
                      onDragEnd={handleDragEnd}
                      className={`w-10 h-10 select-none ${
                        !isThinking &&
                        piece[0] === chess.turn() &&
                        chess.turn() === playerColor[0]
                          ? "cursor-grab"
                          : "cursor-not-allowed opacity-85"
                      }`}
                    />
                  )}
                </div>
              )
            })
          )}
        </div>

        <div className="bg-neutral-800 text-white rounded-xl p-4 w-72 shadow-xl">
          <h2 className="text-xl font-semibold mb-3">Analysis</h2>

          <div className="space-y-2 text-sm">
            <p>
              <span className="text-neutral-400">Last bot move:</span>{" "}
              {lastBotMove ?? "—"}
            </p>
            <p>
              <span className="text-neutral-400">Source:</span>{" "}
              {lastSource ?? "—"}
            </p>
            <p>
              <span className="text-neutral-400">Engine eval:</span>{" "}
              {engineEval ?? "—"}
            </p>
            <p>
              <span className="text-neutral-400">Model eval:</span>{" "}
              {modelEval ?? "—"}
            </p>
            <p>
              <span className="text-neutral-400">FEN:</span>
            </p>
            <p className="break-all text-xs text-neutral-300">{chess.fen()}</p>
          </div>

          <button
            onClick={() => resetBoard(playerColor)}
            className="mt-5 w-full px-4 py-2 bg-white text-black rounded-lg font-semibold hover:opacity-90"
          >
            Reset Board
          </button>
        </div>
      </div>
    </div>
  )
}