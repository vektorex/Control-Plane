"use client";

import React, { useState } from 'react';

export default function PromotionControls({ onPromote }) {
  const [promoted, setPromoted] = useState(false);
  const [isPromoting, setIsPromoting] = useState(false);

  const handlePromote = async () => {
    setIsPromoting(true);
    setTimeout(() => {
      setPromoted(true);
      setIsPromoting(false);
      if (onPromote) {
        onPromote();
      }
    }, 800);
  };

  return (
    <div className="bg-gray-800 p-8 rounded-xl border border-purple-500/30 text-center space-y-4">
      <h2 className="text-xl font-bold text-white">
        {promoted ? "Promotion Initiated" : "Ready for Production"}
      </h2>
      <p className="text-gray-400 max-w-md mx-auto">
        {promoted
          ? "Traffic cutover in progress. Progressive delivery gates are actively monitoring telemetry."
          : "All preconditions, impacts, decisions, freezes, locks, and approvals have been verified."}
      </p>
      {promoted ? (
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 border border-green-500/40 rounded-lg text-sm font-semibold">
          <span>✓ Active Deployment in Progress</span>
        </div>
      ) : (
        <button
          onClick={handlePromote}
          disabled={isPromoting}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold rounded-lg shadow-lg shadow-purple-900/50 transition cursor-pointer"
        >
          {isPromoting ? "PROMOTING..." : "PROMOTE TO PRODUCTION"}
        </button>
      )}
    </div>
  );
}
