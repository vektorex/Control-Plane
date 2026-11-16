"use client";

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { intentService } from '@/services/intent';

export default function IntentWorkspace() {
  const [intent, setIntent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [recentIntents, setRecentIntents] = useState([]);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [recentError, setRecentError] = useState(null);
  const router = useRouter();

  const loadRecentIntents = useCallback(async () => {
    setLoadingRecent(true);
    setRecentError(null);
    try {
      const data = await intentService.listIntents();
      setRecentIntents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.warn("Could not load recent intents:", err);
      setRecentError(err?.message || "Failed to load recent intents.");
    } finally {
      setLoadingRecent(false);
    }
  }, []);

  useEffect(() => {
    loadRecentIntents();
  }, [loadRecentIntents]);

  const handleSynthesize = async (e) => {
    if (e) e.preventDefault();
    if (!intent.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const res = await intentService.createIntent({
        raw_intent: intent.trim(),
      });
      if (res?.id) {
        router.push(`/app/intent/${res.id}`);
      } else {
        throw new Error("Invalid response from intent service.");
      }
    } catch (err) {
      console.warn("Intent request creation failed:", err);
      setSubmitError(err?.message || "Failed to synthesize solution. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto min-h-screen flex flex-col">
      <div className="mb-10 text-center mt-12">
        <h1 className="text-4xl font-bold mb-4">What do you want to build?</h1>
        <p className="text-gray-500 text-lg max-w-2xl mx-auto">
          Describe your objective in plain English. We will analyze requirements, discover governed capabilities, and synthesize candidate solutions for your review.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden mb-12">
        <textarea 
          className="w-full h-40 p-6 text-lg focus:outline-none resize-none"
          placeholder="e.g. 'Review this GitHub repository for security vulnerabilities and create a verified report for the management team...'"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
        ></textarea>

        {submitError && (
          <div className="px-6 py-3 bg-red-50 border-t border-red-100 text-red-600 text-sm">
            {submitError}
          </div>
        )}

        <div className="bg-gray-50 p-4 border-t border-gray-100 flex flex-wrap gap-4 justify-between items-center">
          <div className="flex flex-wrap gap-2">
            <button 
              type="button"
              onClick={() => setIntent("Perform comprehensive data analysis on quarterly financial spreadsheets and summarize key trends.")}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 cursor-pointer transition"
            >
              Data Analysis
            </button>
            <button 
              type="button"
              onClick={() => setIntent("Review repository codebase and dependencies for security vulnerabilities and produce an audit report.")}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 cursor-pointer transition"
            >
              Security Review
            </button>
            <button 
              type="button"
              onClick={() => setIntent("Extract structured entities and key metrics from uploaded PDF documents into JSON.")}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 cursor-pointer transition"
            >
              Document Processing
            </button>
          </div>
          <button 
            type="button"
            onClick={handleSynthesize}
            disabled={isSubmitting || !intent.trim()}
            className="px-6 py-2 bg-black text-white font-medium rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting ? "Synthesizing..." : "Synthesize Solution"}
          </button>
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold text-gray-900 text-lg">Recent Intent Requests</h3>
          <button 
            onClick={loadRecentIntents} 
            className="text-xs text-gray-500 hover:text-black transition"
            type="button"
          >
            Refresh
          </button>
        </div>

        {recentError ? (
          <div className="p-6 border border-red-200 bg-red-50 rounded-xl text-center space-y-2">
            <p className="text-red-600 text-sm">{recentError}</p>
            <button
              onClick={loadRecentIntents}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition"
            >
              Retry
            </button>
          </div>
        ) : loadingRecent ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse p-4 border border-gray-200 rounded-xl bg-white flex justify-between items-center">
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-64"></div>
                  <div className="h-3 bg-gray-100 rounded w-28"></div>
                </div>
                <div className="h-5 bg-gray-200 rounded w-20"></div>
              </div>
            ))}
          </div>
        ) : recentIntents.length > 0 ? (
          <div className="space-y-3">
            {recentIntents.map((req) => (
              <Link key={req.id} href={`/app/intent/${req.id}`}>
                <div className="p-4 border border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-sm cursor-pointer bg-white flex justify-between items-center transition-all">
                  <div>
                    <h4 className="font-medium text-gray-900 line-clamp-1">
                      {req.raw_intent || req.title || `Intent Request #${String(req.id).slice(0, 8)}`}
                    </h4>
                    <p className="text-xs text-gray-500 mt-1">
                      {req.created_at ? new Date(req.created_at).toLocaleDateString() : "Recently submitted"}
                    </p>
                  </div>
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                    req.status === 'completed' || req.status === 'synthesized'
                      ? 'bg-green-100 text-green-800'
                      : req.status === 'failed'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {req.status || "Pending"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 border-2 border-dashed border-gray-200 rounded-xl text-center space-y-2">
            <p className="text-gray-500 text-sm">No recent intent requests found.</p>
            <p className="text-gray-400 text-xs">Enter your goal above and click "Synthesize Solution" to begin.</p>
          </div>
        )}
      </div>
    </div>
  );
}
