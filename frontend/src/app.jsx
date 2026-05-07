import { useMemo, useState } from "react"
import { Chess } from "chess.js"

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
const PIECE_ORDER = ["P", "N", "B", "R", "Q"]
const SQUARE_PX = 64

function getBoardFromFen(chess) {
  const board = Array.from({ length: 8 }, () => Array(8).fill(null))
  const position = chess.board()
  for (let row = 0; row < 8; row++)
    for (let col = 0; col < 8; col++) {
      const p = position[row][col]
      if (p) board[row][col] = p.color + p.type.toUpperCase()
    }
  return board
}

const toSquare = (row, col) => FILES[col] + (8 - row)

function getCaptured(chess) {
  const start = { P: 8, N: 2, B: 2, R: 2, Q: 1 }
  const remaining = { w: { P: 0, N: 0, B: 0, R: 0, Q: 0 }, b: { P: 0, N: 0, B: 0, R: 0, Q: 0 } }
  for (const row of chess.board())
    for (const sq of row) {
      if (sq && sq.type !== "k") remaining[sq.color][sq.type.toUpperCase()]++
    }
  const captured = { w: [], b: [] }
  for (const color of ["w", "b"])
    for (const t of PIECE_ORDER) {
      const diff = start[t] - remaining[color][t]
      for (let i = 0; i < diff; i++) captured[color].push(color + t)
    }
  return captured
}

const evalToBar = (cp) => {
  if (cp == null) return 0.5
  const c = Math.max(-1500, Math.min(1500, cp))
  return 1 / (1 + Math.exp(-c / 400))
}

const formatCp = (cp) => {
  if (cp == null) return "0.00"
  if (Math.abs(cp) >= 9000) return cp > 0 ? "M" : "−M"
  const sign = cp > 0 ? "+" : ""
  return sign + (cp / 100).toFixed(2)
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
  const [lastMoveSquares, setLastMoveSquares] = useState(null)
  const [playerColor, setPlayerColor] = useState("white")
  const [moveHistory, setMoveHistory] = useState([])

  const botColor = playerColor === "white" ? "black" : "white"
  const isFlipped = playerColor === "black"
  const displayRows = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7]
  const displayCols = isFlipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7]
  const captured = useMemo(() => getCaptured(chess), [chess])
  const inCheck = chess.inCheck()

  async function requestBotMove(c, color) {
    try {
      const res = await fetch("http://localhost:5001/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: c.fen(), pgn_so_far: c.pgn(), color }),
      })
      return await res.json()
    } catch (e) {
      console.error(e)
      return null
    }
  }

  async function makeBotMove(currentChess, color) {
    setStatus("NECAI is thinking…")
    setIsThinking(true)
    const data = await requestBotMove(currentChess, color)
    if (!data) { setStatus("Backend offline"); setIsThinking(false); return }

    if (data.game_over) {
      setStatus(`Game over — ${data.reason ?? "finished"}`)
      setLastSource(data.source ?? null)
      setEngineEval(data.engine_eval ?? null)
      setModelEval(data.model_eval ?? null)
      setIsThinking(false)
      return
    }
    if (!data.move_uci) {
      setStatus(data.message || "No move returned")
      setIsThinking(false)
      return
    }

    const next = new Chess(currentChess.fen())
    const move = next.move({
      from: data.move_uci.slice(0, 2),
      to: data.move_uci.slice(2, 4),
      promotion: data.move_uci.length === 5 ? data.move_uci[4] : "q",
    })
    if (!move) { setStatus("Invalid move from backend"); setIsThinking(false); return }

    setChess(next)
    setBoard(getBoardFromFen(next))
    setMoveHistory(next.history())
    setLastBotMove(data.move || data.move_uci)
    setLastMoveSquares({ from: data.move_uci.slice(0, 2), to: data.move_uci.slice(2, 4) })
    setLastSource(data.source ?? null)
    setEngineEval(data.engine_eval ?? null)
    setModelEval(data.model_eval ?? null)

    if (next.isCheckmate()) setStatus("Checkmate")
    else if (next.isStalemate()) setStatus("Stalemate")
    else if (next.inCheck()) setStatus("Check")
    else setStatus("Your move")
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
    setDraggedFrom({ row, col })
    setLegalTargets(chess.moves({ square: from, verbose: true }).map((m) => m.to))
  }

  async function handleDrop(row, col) {
    if (!draggedFrom || isThinking) return
    if (chess.turn() !== playerColor[0]) return

    const from = toSquare(draggedFrom.row, draggedFrom.col)
    const to = toSquare(row, col)
    const next = new Chess(chess.fen())
    const move = next.move({ from, to, promotion: "q" })
    setDraggedFrom(null)
    setLegalTargets([])
    if (!move) return

    setChess(next)
    setBoard(getBoardFromFen(next))
    setMoveHistory(next.history())
    setLastMoveSquares({ from, to })

    if (next.isCheckmate()) { setStatus("Checkmate"); return }
    if (next.isStalemate()) { setStatus("Stalemate"); return }

    await makeBotMove(next, botColor)
  }

  function resetBoard(nextColor = playerColor) {
    const fresh = new Chess()
    setChess(fresh)
    setBoard(getBoardFromFen(fresh))
    setDraggedFrom(null); setLegalTargets([])
    setLastSource(null); setEngineEval(null); setModelEval(null)
    setLastBotMove(null); setLastMoveSquares(null)
    setMoveHistory([]); setIsThinking(false)
    if (nextColor === "black") {
      setStatus("NECAI is thinking…")
      setTimeout(() => makeBotMove(fresh, "white"), 100)
    } else {
      setStatus("Your move")
    }
  }

  const movePairs = []
  for (let i = 0; i < moveHistory.length; i += 2)
    movePairs.push({ num: i / 2 + 1, w: moveHistory[i], b: moveHistory[i + 1] })

  const evalValue = evalToBar(engineEval)
  const whiteHeight = (isFlipped ? 1 - evalValue : evalValue) * 100
  const boardSizePx = SQUARE_PX * 8

  return (
    <div className="h-screen w-full bg-[#0c0c10] text-neutral-100 overflow-hidden flex">
      {/* LEFT RAIL */}
      <aside className="hidden lg:flex flex-col gap-4 w-64 border-r border-neutral-800/80 bg-[#0a0a0e] px-5 py-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <h1 className="text-xl font-bold tracking-tight">NECAI</h1>
          </div>
          <p className="text-[11px] uppercase tracking-widest text-neutral-500 mt-1">
            Neural-Enhanced AI
          </p>
        </div>

        <div className="flex flex-col gap-2 mt-2">
          <ColorButton active={playerColor === "white"} onClick={() => { setPlayerColor("white"); resetBoard("white") }}>
            <PieceIcon color="w" /> Play as White
          </ColorButton>
          <ColorButton active={playerColor === "black"} onClick={() => { setPlayerColor("black"); resetBoard("black") }}>
            <PieceIcon color="b" /> Play as Black
          </ColorButton>
        </div>

        <button
          onClick={() => resetBoard(playerColor)}
          className="mt-1 w-full px-4 py-2.5 bg-amber-400 hover:bg-amber-300 text-black rounded-lg font-semibold text-sm transition-colors"
        >
          New Game
        </button>

        <div className="mt-auto space-y-3">
          <Stat label="Source" value={lastSource ?? "—"} />
          <Stat label="Last move" value={lastBotMove ?? "—"} mono />
          <Stat label="Classical" value={formatCp(engineEval)} mono />
          <Stat label="Neural" value={modelEval == null ? "—" : modelEval.toFixed(3)} mono />
        </div>
      </aside>

      {/* MAIN BOARD AREA */}
      <main className="flex-1 flex flex-col items-center justify-center px-6">
        {/* Top player card */}
        <PlayerCard
          name={isFlipped ? "You" : "NECAI"}
          subtitle={isFlipped ? "Human" : "Bot · classical search"}
          captured={captured[isFlipped ? "b" : "w"]}
          isTurn={chess.turn() === (isFlipped ? "b" : "w")}
          width={boardSizePx}
        />

        <div className="flex items-stretch gap-3 mt-3 mb-3">
          {/* Eval bar */}
          <div
            className="relative w-3 rounded-md overflow-hidden bg-neutral-900 border border-neutral-800"
            style={{ height: boardSizePx }}
          >
            <div
              className="absolute bottom-0 left-0 w-full bg-neutral-100 transition-all duration-500 ease-out"
              style={{ height: `${whiteHeight}%` }}
            />
            <div
              className="absolute left-0 right-0 h-px bg-amber-400/60"
              style={{ bottom: "50%" }}
            />
          </div>

          {/* Board with coordinates */}
          <div className="relative">
            <div className="absolute -left-4 top-0 h-full flex flex-col text-[10px] text-neutral-500 font-mono">
              {displayRows.map((r) => (
                <div key={r} className="flex items-center justify-center" style={{ height: SQUARE_PX }}>
                  {8 - r}
                </div>
              ))}
            </div>
            <div className="absolute -bottom-4 left-0 w-full flex text-[10px] text-neutral-500 font-mono">
              {displayCols.map((c) => (
                <div key={c} className="flex items-center justify-center" style={{ width: SQUARE_PX }}>
                  {FILES[c]}
                </div>
              ))}
            </div>

            <div
              className="grid grid-cols-8 rounded-md overflow-hidden ring-1 ring-neutral-700/40 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.8)]"
              style={{ width: boardSizePx, height: boardSizePx }}
            >
              {displayRows.flatMap((row) =>
                displayCols.map((col) => {
                  const piece = board[row][col]
                  const isLight = (row + col) % 2 === 0
                  const square = toSquare(row, col)
                  const isLegalTarget = legalTargets.includes(square)
                  const isLastMove = lastMoveSquares && (square === lastMoveSquares.from || square === lastMoveSquares.to)
                  const isCheckedKing = inCheck && piece && piece[1] === "K" && piece[0] === chess.turn()
                  const isDragSource = draggedFrom && draggedFrom.row === row && draggedFrom.col === col

                  return (
                    <div
                      key={`${row}-${col}`}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => handleDrop(row, col)}
                      className={[
                        "relative flex items-center justify-center",
                        isLight ? "bg-[#ebd9b3]" : "bg-[#7a5235]",
                        isLastMove ? "outline outline-2 outline-amber-400/70 -outline-offset-2" : "",
                        isCheckedKing ? "bg-[radial-gradient(circle,rgba(239,68,68,0.85)_0%,rgba(239,68,68,0.35)_75%)]" : "",
                        isDragSource ? "brightness-90" : "",
                      ].join(" ")}
                      style={{ width: SQUARE_PX, height: SQUARE_PX }}
                    >
                      {isLegalTarget && !piece && (
                        <div className="absolute w-3 h-3 rounded-full bg-black/40" />
                      )}
                      {isLegalTarget && piece && (
                        <div className="absolute inset-1 ring-[3px] ring-black/40 ring-inset rounded-sm" />
                      )}

                      {piece && (
                        <img
                          src={`/pieces/${piece}.svg`}
                          alt={piece}
                          draggable={!isThinking && piece[0] === chess.turn() && chess.turn() === playerColor[0]}
                          onDragStart={(e) => handleDragStart(e, row, col)}
                          onDragEnd={() => { setDraggedFrom(null); setLegalTargets([]) }}
                          className={[
                            "select-none drop-shadow-[0_3px_4px_rgba(0,0,0,0.5)]",
                            !isThinking && piece[0] === chess.turn() && chess.turn() === playerColor[0]
                              ? "cursor-grab active:cursor-grabbing"
                              : "cursor-not-allowed",
                          ].join(" ")}
                          style={{ width: SQUARE_PX - 8, height: SQUARE_PX - 8 }}
                        />
                      )}
                    </div>
                  )
                }),
              )}
            </div>
          </div>
        </div>

        {/* Bottom player card */}
        <PlayerCard
          name={isFlipped ? "NECAI" : "You"}
          subtitle={isFlipped ? "Bot · classical search" : "Human"}
          captured={captured[isFlipped ? "w" : "b"]}
          isTurn={chess.turn() === (isFlipped ? "w" : "b")}
          width={boardSizePx}
        />
      </main>

      {/* RIGHT RAIL */}
      <aside className="hidden lg:flex flex-col w-72 border-l border-neutral-800/80 bg-[#0a0a0e] px-5 py-6 gap-5">
        <div>
          <div
            className={[
              "rounded-xl px-4 py-3 border",
              isThinking
                ? "border-amber-400/40 bg-amber-400/5"
                : status === "Check"
                ? "border-red-500/40 bg-red-500/5"
                : status === "Checkmate" || status === "Stalemate" || status.startsWith("Game over")
                ? "border-rose-500/40 bg-rose-500/5"
                : "border-neutral-800 bg-neutral-900/40",
            ].join(" ")}
          >
            <p
              className={[
                "text-base font-semibold",
                isThinking ? "text-amber-300 animate-pulse" : "text-neutral-100",
              ].join(" ")}
            >
              {status}
            </p>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              {chess.turn() === "w" ? "White" : "Black"} to move
            </p>
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <h2 className="text-[11px] uppercase tracking-widest text-neutral-500 font-semibold mb-2">
            Moves
          </h2>
          <div className="flex-1 overflow-auto rounded-lg border border-neutral-800 bg-neutral-900/40">
            {movePairs.length === 0 ? (
              <p className="text-xs text-neutral-600 p-3">No moves yet</p>
            ) : (
              <table className="w-full text-sm">
                <tbody>
                  {movePairs.map((p) => (
                    <tr key={p.num} className="border-b border-neutral-800/50 last:border-0">
                      <td className="py-1.5 px-3 text-neutral-500 w-10 text-xs font-mono">{p.num}.</td>
                      <td className="py-1.5 px-2 text-neutral-100 font-mono">{p.w}</td>
                      <td className="py-1.5 px-2 text-neutral-100 font-mono">{p.b ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <details className="text-xs">
          <summary className="cursor-pointer text-neutral-500 hover:text-neutral-300 transition">FEN</summary>
          <p className="break-all mt-2 text-neutral-400 leading-snug font-mono text-[10px]">
            {chess.fen()}
          </p>
        </details>
      </aside>
    </div>
  )
}

function ColorButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={[
        "flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all border",
        active
          ? "bg-neutral-100 text-black border-neutral-100"
          : "bg-neutral-900 text-neutral-300 border-neutral-800 hover:border-neutral-700 hover:bg-neutral-800",
      ].join(" ")}
    >
      {children}
    </button>
  )
}

function PieceIcon({ color }) {
  return (
    <div className={[
      "w-4 h-4 rounded-full",
      color === "w" ? "bg-white border border-neutral-300" : "bg-neutral-900 border border-neutral-700",
    ].join(" ")} />
  )
}

function Stat({ label, value, mono }) {
  return (
    <div className="flex justify-between items-center text-xs">
      <span className="text-neutral-500">{label}</span>
      <span className={[mono ? "font-mono" : "", "text-neutral-200"].join(" ")}>{value}</span>
    </div>
  )
}

function PlayerCard({ name, subtitle, captured, isTurn, width }) {
  return (
    <div
      className={[
        "flex items-center gap-3 px-3 py-2 rounded-lg border transition-colors",
        isTurn ? "border-amber-400/50 bg-amber-400/5" : "border-neutral-800 bg-neutral-900/40",
      ].join(" ")}
      style={{ width }}
    >
      <div className={[
        "w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold",
        isTurn ? "bg-amber-400 text-black" : "bg-neutral-800 text-neutral-400",
      ].join(" ")}>
        {name[0]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold leading-tight">{name}</p>
        <p className="text-[10px] text-neutral-500 leading-tight">{subtitle}</p>
      </div>
      <div className="flex items-center gap-0 flex-wrap max-w-[180px] justify-end">
        {captured.map((p, i) => (
          <img key={i} src={`/pieces/${p}.svg`} alt={p} className="w-4 h-4 -ml-0.5" />
        ))}
      </div>
    </div>
  )
}
