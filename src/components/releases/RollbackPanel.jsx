"use client";

import React, { useState } from 'react';

export default function RollbackPanel({ onRollback }) {
  const [requested, setRequested] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleConfirm = () => {
    setRequested(true);
    setShowConfirm(false);
    if (onRollback) {
      onRollback();
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <p className="text-gray-400 mb-4 text-sm">
        If verification fails or telemetry degrades, initiate rollback to source_version.
      </p>

      {requested ? (
        <div className="p-3 bg-red-900/30 border border-red-500/40 rounded-lg text-red-300 text-sm flex items-center gap-2">
          <span>⚠ Rollback request queued. Traffic rerouting back to source release.</span>
        </div>
      ) : showConfirm ? (
        <div className="p-4 bg-gray-900 border border-red-800/60 rounded-lg space-y-3">
          <p className="text-xs text-red-400 font-semibold">
            Are you sure you want to request a full rollback to the previous version?
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleConfirm}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-semibold cursor-pointer"
            >
              Confirm Rollback
            </button>
            <button
              onClick={() => setShowConfirm(false)}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-xs cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowConfirm(true)}
          className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-800 rounded hover:bg-red-600/30 transition text-sm font-medium cursor-pointer"
        >
          Request Rollback
        </button>
      )}
    </div>
  );
}
