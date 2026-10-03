"use client";

import React, { useState } from "react";
import { MessageSquare, Bot, User, CornerDownRight, CheckCircle2, Trash2, Send } from "lucide-react";

export function CommentThread({
  comments = [],
  currentUserId,
  onAddComment,
  onResolveComment,
  onDeleteComment,
}) {
  const [newCommentBody, setNewCommentBody] = useState("");
  const [replyingToId, setReplyingToId] = useState(null);
  const [replyBody, setReplyBody] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Group top-level and children
  const topLevel = comments.filter((c) => !c.parent_comment_id);
  const repliesByParent = comments.reduce((acc, c) => {
    if (c.parent_comment_id) {
      acc[c.parent_comment_id] = acc[c.parent_comment_id] || [];
      acc[c.parent_comment_id].push(c);
    }
    return acc;
  }, {});

  const handlePostTopLevel = async (e) => {
    e.preventDefault();
    if (!newCommentBody.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onAddComment({ body: newCommentBody });
      setNewCommentBody("");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePostReply = async (parentId) => {
    if (!replyBody.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onAddComment({ body: replyBody, parent_comment_id: parentId });
      setReplyBody("");
      setReplyingToId(null);
    } finally {
      setSubmitting(false);
    }
  };

  const renderComment = (comment, isReply = false) => {
    const isAi = comment.author_type === "ai";
    const isDeleted = comment.status === "deleted";
    const isResolved = comment.status === "resolved";

    return (
      <div
        key={comment.id}
        className={`p-3 rounded-lg border transition-all ${
          isReply ? "ml-6 bg-slate-900/40 border-slate-800/80" : "bg-slate-900/70 border-slate-800"
        } ${isResolved ? "opacity-60 bg-emerald-950/10 border-emerald-900/30" : ""}`}
      >
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center justify-center w-5 h-5 rounded-full text-[10px] ${
                isAi ? "bg-amber-500/20 text-amber-400" : "bg-indigo-500/20 text-indigo-400"
              }`}
            >
              {isAi ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
            </span>
            <span className="text-xs font-semibold text-slate-200">
              {isAi ? "AI Work Copilot" : comment.author_id.slice(0, 10)}
            </span>
            {isAi && (
              <span className="px-1.5 py-0.2 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[9px] font-medium rounded">
                AI Suggestion
              </span>
            )}
            {isResolved && (
              <span className="px-1.5 py-0.2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[9px] font-medium rounded flex items-center gap-1">
                <CheckCircle2 className="w-2.5 h-2.5" /> Resolved
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-slate-500">
            <span>{new Date(comment.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
            {!isDeleted && (
              <div className="flex items-center gap-1 ml-2">
                {!isReply && (
                  <button
                    onClick={() => setReplyingToId(replyingToId === comment.id ? null : comment.id)}
                    className="p-1 hover:text-indigo-400 transition-colors"
                    title="Reply"
                  >
                    <CornerDownRight className="w-3 h-3" />
                  </button>
                )}
                {onResolveComment && !isResolved && (
                  <button
                    onClick={() => onResolveComment(comment.id)}
                    className="p-1 hover:text-emerald-400 transition-colors"
                    title="Mark resolved"
                  >
                    <CheckCircle2 className="w-3 h-3" />
                  </button>
                )}
                {onDeleteComment && (
                  <button
                    onClick={() => onDeleteComment(comment.id)}
                    className="p-1 hover:text-rose-400 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        <p className={`text-xs ${isDeleted ? "italic text-slate-500" : "text-slate-300"} leading-relaxed`}>
          {comment.body}
        </p>

        {/* Mentions tags */}
        {comment.mentions && comment.mentions.length > 0 && !isDeleted && (
          <div className="flex items-center gap-1 mt-2">
            {comment.mentions.map((m) => (
              <span
                key={m.id || m.mentioned_user_id}
                className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px]"
              >
                @{m.mentioned_user_id.slice(0, 8)}
              </span>
            ))}
          </div>
        )}

        {/* Reply form */}
        {replyingToId === comment.id && (
          <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center gap-2">
            <input
              type="text"
              value={replyBody}
              onChange={(e) => setReplyBody(e.target.value)}
              placeholder="Write a reply..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={() => handlePostReply(comment.id)}
              disabled={submitting || !replyBody.trim()}
              className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded text-xs font-medium transition-colors"
            >
              Reply
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between text-xs font-medium text-slate-400">
        <div className="flex items-center gap-1.5">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <span>Threaded Discussion ({comments.length})</span>
        </div>
      </div>

      <div className="flex flex-col gap-2 max-h-[420px] overflow-y-auto pr-1">
        {topLevel.length === 0 ? (
          <div className="text-center py-6 text-slate-500 text-xs">
            No comments yet. Start the conversation with collaborators or AI.
          </div>
        ) : (
          topLevel.map((c) => (
            <div key={c.id} className="flex flex-col gap-1.5">
              {renderComment(c)}
              {repliesByParent[c.id]?.map((rep) => renderComment(rep, true))}
            </div>
          ))
        )}
      </div>

      <form onSubmit={handlePostTopLevel} className="flex items-center gap-2 pt-2 border-t border-slate-800">
        <input
          type="text"
          value={newCommentBody}
          onChange={(e) => setNewCommentBody(e.target.value)}
          placeholder="Share feedback, notes, or use @user to mention..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
        <button
          type="submit"
          disabled={submitting || !newCommentBody.trim()}
          className="flex items-center gap-1 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Comment</span>
        </button>
      </form>
    </div>
  );
}
