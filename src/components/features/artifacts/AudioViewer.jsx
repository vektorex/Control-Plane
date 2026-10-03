"use client";

import React, { useState, useRef } from "react";
import { Play, Pause, Volume2, Clock, User, Headphones } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function AudioViewer({ artifact, parts = [], onSelectTimestamp }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(artifact?.metadata?.duration_seconds || 0);
  const audioRef = useRef(null);

  // Find audio segment parts or transcript parts
  const audioParts = parts.filter((p) => p.part_type === "audio_segment" || p.part_type === "text");

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current && audioRef.current.duration) {
      setDuration(audioRef.current.duration);
    }
  };

  const jumpTo = (secs) => {
    if (audioRef.current) {
      audioRef.current.currentTime = secs;
      setCurrentTime(secs);
      if (!isPlaying) {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
    if (onSelectTimestamp) onSelectTimestamp(secs);
  };

  const formatTime = (secs) => {
    if (secs == null || isNaN(secs)) return "00:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // Structured transcripts from metadata or parts
  const transcriptSegments = artifact?.metadata?.transcript_segments || audioParts.map((p, idx) => ({
    timestamp: p.metadata?.timestamp ?? idx * 10,
    speaker: p.metadata?.speaker || null, // only expose if provider returned real speaker
    text: p.text_content || p.metadata?.text || "",
  })).filter((s) => s.text);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden flex flex-col h-[550px]">
      {/* Audio Player Header */}
      <div className="p-4 border-b border-zinc-800 bg-zinc-950/70 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-200">
            <Headphones className="h-4 w-4 text-cyan-400" />
            <span>Audio Intelligence</span>
          </div>
          <Badge variant="outline" className="text-[10px] text-zinc-400 border-zinc-700">
            Duration: {formatTime(duration)}
          </Badge>
        </div>

        {/* Hidden or styled audio element */}
        <audio
          ref={audioRef}
          src={`/api/artifacts/${artifact?.id}/raw`}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={() => setIsPlaying(false)}
        />

        {/* Controls */}
        <div className="flex items-center gap-4 bg-zinc-900/90 p-3 rounded-lg border border-zinc-800">
          <Button
            size="sm"
            onClick={togglePlay}
            className="h-9 w-9 rounded-full p-0 bg-cyan-600 hover:bg-cyan-500 text-white"
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
          </Button>

          <div className="flex-1 space-y-1">
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={(e) => jumpTo(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] font-mono text-zinc-400">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Transcript Stream */}
      <div className="flex-1 bg-zinc-950 p-4 overflow-y-auto space-y-3">
        <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
          Timestamped Transcript
        </h4>

        {transcriptSegments.length > 0 ? (
          transcriptSegments.map((seg, idx) => {
            const isCurrent = currentTime >= seg.timestamp && (idx === transcriptSegments.length - 1 || currentTime < transcriptSegments[idx + 1].timestamp);

            return (
              <div
                key={idx}
                onClick={() => jumpTo(seg.timestamp)}
                className={`p-3 rounded-lg border transition-colors cursor-pointer flex gap-3 ${
                  isCurrent
                    ? "bg-cyan-950/30 border-cyan-800/60 shadow-sm"
                    : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700"
                }`}
              >
                <div className="flex flex-col items-center gap-1 shrink-0 pt-0.5">
                  <span className="inline-flex items-center gap-1 font-mono text-[11px] text-cyan-400 bg-zinc-800/80 px-1.5 py-0.5 rounded">
                    <Clock className="h-3 w-3" />
                    {formatTime(seg.timestamp)}
                  </span>
                  {seg.speaker && (
                    <span className="text-[10px] text-zinc-400 flex items-center gap-0.5 font-medium">
                      <User className="h-2.5 w-2.5" />
                      {seg.speaker}
                    </span>
                  )}
                </div>

                <p className="text-xs text-zinc-200 leading-relaxed flex-1">
                  {seg.text}
                </p>
              </div>
            );
          })
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-zinc-500 text-xs">
            <Clock className="h-8 w-8 text-zinc-600 mb-2" />
            <p>No audio transcript segments available.</p>
            <p className="text-[10px] text-zinc-600 mt-1">
              Audio transcription provider extracts timestamped utterance records.
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-zinc-950/80 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
        <span>File: <strong className="text-zinc-200">{artifact?.filename}</strong></span>
        <Badge variant="secondary" className="text-[10px]">
          Grounded Timestamp Citations
        </Badge>
      </div>
    </div>
  );
}
