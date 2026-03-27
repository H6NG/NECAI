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

  function handleDragStart(row, col) {
    const from = toSquare(row, col)
    const piece = chess.get(from)

    if (!piece || piece.color !== chess.turn()) return

    const moves = chess.moves({ square: from, verbose: true })
    setDraggedFrom({ row, col })
    setLegalTargets(moves.map((move) => move.to))
  }

  function handleDragOver(e) {
    e.preventDefault()
  }

  function handleDrop(row, col) {
    if (!draggedFrom) return

    const from = toSquare(draggedFrom.row, draggedFrom.col)
    const to = toSquare(row, col)

    const next = new Chess(chess.fen())
    const move = next.move({
      from,
      to,
      promotion: "q",
    })

    if (!move) {
      setDraggedFrom(null)
      setLegalTargets([])
      return
    }

    setChess(next)
    setBoard(getBoardFromFen(next))
    setDraggedFrom(null)
    setLegalTargets([])
  }

  function handleDragEnd() {
    setDraggedFrom(null)
    setLegalTargets([])
  }

  function resetBoard() {
    const fresh = new Chess()
    setChess(fresh)
    setBoard(getBoardFromFen(fresh))
    setDraggedFrom(null)
    setLegalTargets([])
  }

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col items-center justify-center p-6">
      <h1 className="text-white text-3xl font-bold mb-2">Chess Board</h1>
      <p className="text-neutral-300 mb-5">
        Turn: {chess.turn() === "w" ? "White" : "Black"}
      </p>

      <div className="grid grid-cols-8 border-4 border-neutral-700 shadow-2xl">
        {board.flatMap((row, rowIndex) =>
          row.map((piece, colIndex) => {
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
                    draggable={piece[0] === chess.turn()}
                    onDragStart={() => handleDragStart(rowIndex, colIndex)}
                    onDragEnd={handleDragEnd}
                    className={`w-10 h-10 select-none ${
                      piece[0] === chess.turn()
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

      <button
        onClick={resetBoard}
        className="mt-6 px-4 py-2 bg-white text-black rounded-lg font-semibold hover:opacity-90"
      >
        Reset Board
      </button>
    </div>
  )
}