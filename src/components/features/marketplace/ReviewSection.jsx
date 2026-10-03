"use client";

import React, { useState } from "react";
import { Star, MessageSquare, ShieldCheck, AlertCircle, Send, CheckCircle2 } from "lucide-react";
import { marketplaceService } from "@/services/marketplace";

export function ReviewSection({ packageId, reviews = [], onReviewSubmitted }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await marketplaceService.submitReview(packageId, {
        rating: Number(rating),
        review: comment.trim(),
      });
      setSuccess(true);
      setComment("");
      onReviewSubmitted?.();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err?.message || "Failed to submit review.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Notice regarding user ratings */}
      <div className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/60 dark:bg-neutral-800/30 flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 text-neutral-400 shrink-0 mt-0.5" />
        <p className="text-[11px] text-neutral-500 dark:text-neutral-400 leading-relaxed">
          Reviews and star ratings represent subjective, user-submitted feedback. The platform displays factual arithmetic averages and does not generate automated or authoritative &quot;quality scores&quot; based on reviews.
        </p>
      </div>

      {/* Submit Review Form */}
      <form onSubmit={handleSubmit} className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-xs space-y-3">
        <h4 className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 flex items-center gap-1.5">
          <MessageSquare className="w-3.5 h-3.5 text-blue-500" />
          Leave a Review
        </h4>

        <div className="flex items-center gap-1">
          <span className="text-xs text-neutral-500 mr-2">Rating:</span>
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              type="button"
              key={star}
              onClick={() => setRating(star)}
              className="p-1 text-amber-400 hover:scale-110 transition-transform"
            >
              <Star
                className={`w-4 h-4 ${
                  star <= rating ? "fill-amber-400 text-amber-400" : "text-neutral-300 dark:text-neutral-600"
                }`}
              />
            </button>
          ))}
          <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300 ml-2">
            {rating} of 5 stars
          </span>
        </div>

        <textarea
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Share your practical experience using this package, template, or work pack..."
          required
          className="w-full px-3 py-2 text-xs rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:ring-1 focus:ring-blue-500 outline-hidden"
        />

        {error && (
          <div className="text-xs text-rose-600 dark:text-rose-400">
            {error}
          </div>
        )}

        {success && (
          <div className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Review submitted successfully!
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting || !comment.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-xs"
          >
            <Send className="w-3 h-3" />
            {submitting ? "Submitting..." : "Submit Review"}
          </button>
        </div>
      </form>

      {/* Review List */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-neutral-900 dark:text-neutral-100">
          Community Reviews ({reviews.length})
        </h4>

        {reviews.length === 0 ? (
          <p className="text-xs text-neutral-400 italic p-4 text-center border border-dashed rounded-xl">
            No reviews yet. Be the first to share your experience with this package.
          </p>
        ) : (
          reviews.map((rev) => (
            <div
              key={rev.id}
              className="p-3.5 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-xs space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star
                      key={s}
                      className={`w-3.5 h-3.5 ${
                        s <= (rev.rating || 5)
                          ? "fill-amber-400 text-amber-400"
                          : "text-neutral-300 dark:text-neutral-700"
                      }`}
                    />
                  ))}
                  <span className="text-[11px] text-neutral-400 ml-2">
                    by Org member • {new Date(rev.created_at).toLocaleDateString()}
                  </span>
                </div>
                {rev.status === "active" && (
                  <span className="flex items-center gap-0.5 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">
                    <ShieldCheck className="w-3 h-3" /> Verified
                  </span>
                )}
              </div>
              <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
                {rev.review}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
