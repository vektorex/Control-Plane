"use client";

import React, { useState } from 'react';

export default function ChangeBuilder({ onProposalParsed }) {
  const [description, setDescription] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [parsedResult, setParsedResult] = useState(null);

  const handleParse = () => {
    if (!description.trim()) return;
    setIsParsing(true);
    setTimeout(() => {
      const result = {
        title: "Model Replacement for GitHub Security Review",
        targetResource: "workflow/github-sec-review",
        proposedChange: "Update model configuration to gpt-4o",
        impactRisk: "low",
        timestamp: new Date().toISOString()
      };
      setParsedResult(result);
      setIsParsing(false);
      if (onProposalParsed) {
        onProposalParsed(result);
      }
    }, 600);
  };

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Natural Language Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          rows="3"
          placeholder="E.g. Replace the GitHub security workflow's model with another approved model."
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={handleParse}
          disabled={isParsing || !description.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium cursor-pointer"
        >
          {isParsing ? "Parsing Proposal..." : "Parse Change Proposal"}
        </button>
      </div>

      {parsedResult && (
        <div className="p-4 bg-gray-900 border border-gray-700 rounded-lg space-y-2 text-xs">
          <div className="font-semibold text-green-400">✓ Structured Proposal Identified</div>
          <div className="text-gray-300"><span className="text-gray-500">Target:</span> {parsedResult.targetResource}</div>
          <div className="text-gray-300"><span className="text-gray-500">Summary:</span> {parsedResult.proposedChange}</div>
          <div className="text-gray-300"><span className="text-gray-500">Risk Assessment:</span> <span className="text-green-300 uppercase font-bold">{parsedResult.impactRisk}</span></div>
        </div>
      )}
    </div>
  );
}
