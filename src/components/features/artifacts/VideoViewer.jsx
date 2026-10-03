"use client";

import React, { useState, useRef } from "react";
import { Film, Play, Pause, Clock, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function VideoViewer({ artifact, parts = [], onSelectFrame }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeTab, setActiveTab] = useState("frames"); // "frames" | "player"
  const videoRef = useRef(null);

  // Video frames parts
  const frameParts = parts.filter((p) => p.part_type === "video_frame");
  const duration = artifact?.metadata?.duration_seconds || 0;

  const formatTime = (secs) => {
    if (secs == null || isNaN(secs)) return "00:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const jumpToFrame = (frame) => {
    const ts = frame.metadata?.timestamp_seconds ?? 0;
    setCurrentTime(ts);
    if (videoRef.current) {
      videoRef.current.currentTime = ts;
    }
    if (onSelectFrame) onSelectFrame(frame);
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden flex flex-col h-[550px]">
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-950/60">
        <div className="flex items-center gap-3">
          <Film className="h-4 w-4 text-purple-400" />
          <span className="text-xs font-medium text-zinc-200">
            Video Intelligence
          </span>
          <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-700">
            {frameParts.length} Extracted Frames
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("frames")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              activeTab === "frames"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Keyframe Gallery
          </button>
          <button
            onClick={() => setActiveTab("player")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              activeTab === "player"
                ? "bg-zinc-800 text-zinc-100 border border-zinc-700"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Video Player
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 bg-zinc-950 p-4 overflow-y-auto">
        {activeTab === "frames" ? (
          <div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {frameParts.map((frame, idx) => {
                const ts = frame.metadata?.timestamp_seconds ?? idx * 5;
                const frameSrc = frame.content_reference
                  ? `/api/artifacts/parts/${frame.id}/raw`
                  : null;

                return (
                  <div
                    key={frame.id || idx}
                    onClick={() => jumpToFrame(frame)}
                    className="bg-zinc-900 border border-zinc-800 hover:border-purple-600/60 rounded-lg overflow-hidden cursor-pointer group transition-all"
                  >
                    <div className="aspect-video bg-zinc-950 flex items-center justify-center relative">
                      {frameSrc ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={frameSrc}
                          alt={`Frame at ${formatTime(ts)}`}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <ImageIcon className="h-6 w-6 text-zinc-700" />
                      )}
                      <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] font-mono px-1 rounded">
                        {formatTime(ts)}
                      </span>
                    </div>

                    <div className="p-2 text-[11px] text-zinc-400">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-purple-400">Frame #{frame.sequence_number + 1}</span>
                        <span className="text-[10px] text-zinc-500">
                          {frame.metadata?.frame_index ? `Idx ${frame.metadata.frame_index}` : ""}
                        </span>
                      </div>
                      {frame.text_content && (
                        <p className="mt-1 text-[10px] text-zinc-300 line-clamp-2">
                          {frame.text_content}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {frameParts.length === 0 && (
              <div className="h-64 flex flex-col items-center justify-center text-zinc-500 text-xs">
                <Film className="h-8 w-8 text-zinc-600 mb-2" />
                <p>No keyframes extracted yet.</p>
                <p className="text-[10px] text-zinc-600 mt-1">
                  Bounded keyframe sampling extracts up to 30 frames.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center">
            {/* Native HTML5 video with preload=metadata to avoid huge memory consumption */}
            <video
              ref={videoRef}
              src={`/api/artifacts/${artifact?.id}/raw`}
              controls
              preload="metadata"
              className="max-h-[420px] max-w-full rounded-lg border border-zinc-800 shadow-lg"
            />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-zinc-950/80 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-3">
          <span>File: <strong className="text-zinc-200">{artifact?.filename}</strong></span>
          {duration > 0 && (
            <span>Duration: <strong className="text-zinc-200">{formatTime(duration)}</strong></span>
          )}
        </div>
        <Badge variant="secondary" className="text-[10px]">
          Bounded Frame Extraction (&le;30 frames)
        </Badge>
      </div>
    </div>
  );
}
