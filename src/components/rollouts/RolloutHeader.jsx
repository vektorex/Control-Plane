"use client";

import React, { useState } from 'react';

export default function RolloutHeader({ rolloutId, onPause, onAbort }) {
  const [isPaused, setIsPaused] = useState(false);
  const [isAborted, setIsAborted] = useState(false);

  const handleTogglePause = () => {
    const nextState = !isPaused;
    setIsPaused(nextState);
    if (onPause) {
      onPause(nextState);
    }
  };

  const handleAbort = () => {
    setIsAborted(true);
    if (onAbort) {
      onAbort();
    }
  };

  const idDisplay = rolloutId ? rolloutId.slice(0, 8) : "demo-001";

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex justify-between items-center">
      <div>
        <h1 className="text-2xl font-bold text-white">
          Rollout <span className="font-mono text-gray-400 text-lg">#{idDisplay}</span>
        </h1>
        <p className="text-gray-400 mt-1">
          Strategy: <span className="text-purple-400">Percentage Canary</span>
          {isPaused && <span className="ml-2 text-yellow-400 font-semibold">[PAUSED]</span>}
          {isAborted && <span className="ml-2 text-red-400 font-semibold">[ABORTED]</span>}
        </p>
      </div>
      <div className="flex gap-2">
        {!isAborted && (
          <button
            onClick={handleTogglePause}
            className={`px-4 py-2 border rounded font-medium text-sm transition cursor-pointer ${
              isPaused
                ? "bg-green-600/20 text-green-400 border-green-800 hover:bg-green-600/30"
                : "bg-yellow-600/20 text-yellow-400 border-yellow-800 hover:bg-yellow-600/30"
            }`}
          >
            {isPaused ? "Resume" : "Pause"}
          </button>
        )}
        <button
          onClick={handleAbort}
          disabled={isAborted}
          className={`px-4 py-2 border rounded font-medium text-sm transition cursor-pointer ${
            isAborted
              ? "bg-gray-800 text-gray-500 border-gray-700 cursor-not-allowed"
              : "bg-red-600/20 text-red-400 border-red-800 hover:bg-red-600/30"
          }`}
        >
          {isAborted ? "Aborted" : "Abort"}
        </button>
      </div>
    </div>
  );
}
