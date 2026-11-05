"use client";

import React, { useState } from 'react';

export default function RolloutRollback({ onConfirmRollback }) {
  const [confirmed, setConfirmed] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleConfirm = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setConfirmed(true);
      setIsProcessing(false);
      if (onConfirmRollback) {
        onConfirmRollback();
      }
    }, 700);
  };

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-red-500/30 text-center space-y-4">
      <h2 className="text-xl font-bold text-white">
        {confirmed ? "Rollback Dispatched" : "Abort & Rollback"}
      </h2>
      <p className="text-gray-400 max-w-md mx-auto text-sm">
        {confirmed
          ? "The rollout has been terminated and traffic returned to the baseline release candidate."
          : "This will immediately pause the rollout, prevent future stages, and request a full rollback from STEP 53 Releases."}
      </p>
      {confirmed ? (
        <div className="inline-block px-4 py-2 bg-red-900/40 text-red-300 border border-red-700/60 rounded-lg text-sm font-semibold">
          ✓ Rollback in Progress
        </div>
      ) : (
        <button
          onClick={handleConfirm}
          disabled={isProcessing}
          className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold rounded-lg shadow-lg shadow-red-900/50 transition cursor-pointer"
        >
          {isProcessing ? "DISPATCHING..." : "CONFIRM ROLLBACK"}
        </button>
      )}
    </div>
  );
}
