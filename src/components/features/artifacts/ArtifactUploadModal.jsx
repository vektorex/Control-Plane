"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { UploadCloud, File, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { artifactService } from "@/services/artifacts";

const ALLOWED_EXTENSIONS = [
  "png", "jpg", "jpeg", "webp",
  "pdf", "txt", "md", "docx",
  "mp3", "wav", "m4a",
  "mp4", "webm",
  "csv", "xlsx"
];

const MAX_SIZE_MB = 100;

export function ArtifactUploadModal({ isOpen, onClose, onUploaded, projectId = null }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [autoProcess, setAutoProcess] = useState(true);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    const ext = selected.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file format .${ext}. Supported: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }

    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File exceeds maximum size of ${MAX_SIZE_MB}MB.`);
      return;
    }

    setError(null);
    setFile(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (!dropped) return;

    const ext = dropped.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file format .${ext}.`);
      return;
    }

    if (dropped.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File exceeds maximum size of ${MAX_SIZE_MB}MB.`);
      return;
    }

    setError(null);
    setFile(dropped);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const res = await artifactService.uploadArtifact(file, { projectId });
      const artifactId = res.id;

      if (autoProcess && artifactId) {
        try {
          await artifactService.processArtifact(artifactId);
        } catch (procErr) {
          console.warn("Background auto-process dispatched with error:", procErr);
        }
      }

      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setFile(null);
        onClose();
        if (onUploaded) onUploaded(res);
      }, 1000);
    } catch (err) {
      setError(err?.message || "Failed to upload artifact.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Upload Multimodal Artifact">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="border-2 border-dashed border-zinc-700 hover:border-zinc-500 rounded-lg p-6 text-center cursor-pointer transition-colors bg-zinc-900/50"
          onClick={() => document.getElementById("artifact-file-input")?.click()}
        >
          <input
            id="artifact-file-input"
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept={ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(",")}
          />
          <UploadCloud className="mx-auto h-12 w-12 text-zinc-400 mb-2" />
          <p className="text-sm font-medium text-zinc-200">
            {file ? file.name : "Click to browse or drag and drop media"}
          </p>
          <p className="text-xs text-zinc-500 mt-1">
            Images, PDFs, Audio, Video, CSV, Excel (up to {MAX_SIZE_MB}MB)
          </p>
          {file && (
            <div className="mt-3 inline-flex items-center gap-2 text-xs font-mono bg-zinc-800 px-3 py-1 rounded text-zinc-300">
              <File className="h-3.5 w-3.5 text-blue-400" />
              {(file.size / (1024 * 1024)).toFixed(2)} MB
            </div>
          )}
        </div>

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-400 bg-red-950/40 p-3 rounded border border-red-800/50">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-950/40 p-3 rounded border border-emerald-800/50">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <span>Artifact uploaded and scheduled for extraction successfully!</span>
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-zinc-400 bg-zinc-800/40 p-2.5 rounded border border-zinc-700/50">
          <span>Automatically trigger media parts extraction</span>
          <input
            type="checkbox"
            checked={autoProcess}
            onChange={(e) => setAutoProcess(e.target.checked)}
            className="rounded border-zinc-700 bg-zinc-900 text-blue-600 focus:ring-blue-500 h-4 w-4"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={uploading}>
            Cancel
          </Button>
          <Button type="submit" disabled={!file || uploading}>
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              "Upload Artifact"
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
