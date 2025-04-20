import React, { useState, useEffect } from 'react';
import { RefreshCw, Award } from 'lucide-react';
import Board from './components/Board';
import ScoreBoard from './components/ScoreBoard';
import GameHistory from './components/GameHistory';

function App() {
  const API_URL = import.meta.env.VITE_API_URL;

  // Game state
  const [board, setBoard] = useState(Array(9).fill(null));
  const [xIsNext, setXIsNext] = useState(true);
  const [winner, setWinner] = useState<string | null>(null);
  const [scores, setScores] = useState({ X: 0, O: 0, draws: 0 });
  const [gameHistory, setGameHistory] = useState<Array<{
    winner: string | null;
    board: Array<string | null>;
    date: Date;
  }>>([]);
  const [gameStatus, setGameStatus] = useState<'playing' | 'won' | 'draw'>('playing');
  const [winningLine, setWinningLine] = useState<number[] | null>(null);

  // fetches the current state from backend
  useEffect(() => {
    const fetchGameState = async () => {
      try {
        const response = await fetch(`${API_URL}/state`);
        const data = await response.json();
        setBoard(data.board);
        setXIsNext(data.x_is_next);
        setGameStatus(data.status);
        setWinner(data.winner || null);
        setWinningLine(data.winning_line || null);
      } catch (error) {
        console.error("Failed to fetch game state:", error);
      }
    };
    fetchGameState();
  }, [API_URL]);

  useEffect(() => {
    const fetchScores = async () => {
      const response = await fetch(`${API_URL}/scores`);
      const data = await response.json();
      setScores(data);
    };
    fetchScores();
  }, [API_URL]);
  
  useEffect(() => {
    const fetchHistory = async () => {
      const response = await fetch(`${API_URL}/history`);
      const data = await response.json();
      setGameHistory(data);
    };
    fetchHistory();
  }, [API_URL]);

  // Click a square
  const handleClick = async (index: number) => {
    if (board[index] || gameStatus !== 'playing') return;
  
    try {
      const response = await fetch(`${API_URL}/move/${index}`, {
        method: 'POST',
      });
  
      const data = await response.json();
      if (data.error) return;
  
      setBoard(data.board);
      setXIsNext(data.x_is_next);
      setGameStatus(data.status);
      setWinningLine(data.winning_line || null);
      setWinner(data.winner || null);
  
      // Always pull fresh stats/history from backend
      if (data.status === 'won' || data.status === 'draw') {
        const [scoresRes, historyRes] = await Promise.all([
          fetch(`${API_URL}/scores`),
          fetch(`${API_URL}/history`)
        ]);
  
        const scoresData = await scoresRes.json();
        const historyData = await historyRes.json();
  
        setScores(scoresData);
        setGameHistory(historyData);
      }
  
    } catch (error) {
      console.error("Move failed:", error);
    }
  };  

  // Reset the game
  const resetGame = async () => {
    try {
      const response = await fetch(`${API_URL}/reset`, {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reset_stats: false })
      });
      const data = await response.json();
      setBoard(data.board);
      setXIsNext(data.x_is_next);
      setGameStatus('playing');
      setWinningLine(null);
      setWinner(null);
    } catch (error) {
      console.error("Failed to reset game:", error);
    }
  };

  const resetAll = async () => {
    try {
      const response = await fetch(`${API_URL}/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reset_stats: true })
      });
      const data = await response.json();
      setBoard(data.board);
      setXIsNext(data.x_is_next);
      setGameStatus("playing");
      setWinningLine(null);
      setWinner(null);
      setScores(data.scores);
      setGameHistory(data.history);
    } catch (error) {
      console.error("Failed to reset stats:", error);
    }
  };
  
  // Get current game status message
  const getStatusMessage = () => {
    if (gameStatus === 'won' && winner) {
      return `Player ${winner} wins!`;
    } else if (gameStatus === 'draw') {
      return "It's a draw!";
    } else {
      return `Next player: ${xIsNext ? 'X' : 'O'}`;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 to-purple-100 flex flex-col items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 bg-indigo-600 text-white text-center">
          <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
            <Award className="h-8 w-8" />
            Tic Tac Toe
          </h1>
          <p className="text-indigo-200 mt-1">A classic game reimagined</p>
        </div>
        
        <div className="p-6 md:p-8 grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Game section */}
          <div className="md:col-span-2 flex flex-col items-center">
            <div className="mb-4 text-center">
              <h2 className="text-xl font-semibold text-indigo-800">{getStatusMessage()}</h2>
            </div>
            
            <Board 
              squares={board} 
              onClick={handleClick} 
              winningLine={winningLine}
            />
            
            <div className="mt-6 flex gap-4">
              <button 
                onClick={resetGame}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded-lg transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                New Game
              </button>
              <button 
                onClick={resetAll}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-lg transition-colors"
              >
                Reset All
              </button>
            </div>
          </div>
          
          {/* Stats section */}
          <div className="flex flex-col gap-6">
            <ScoreBoard scores={scores} />
            <GameHistory history={gameHistory} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;