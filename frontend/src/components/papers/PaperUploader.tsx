import React, { useState, useRef } from "react";
import { Upload, FileUp, CheckCircle, AlertCircle } from "lucide-react";
import { uploadPaperPdf } from "../../api/papers";
import { useUIStore } from "../../store/useUIStore";

interface PaperUploaderProps {
  onUploadSuccess: () => void;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: "uploading" | "success" | "error";
  errorMessage?: string;
}

export function PaperUploader({ onUploadSuccess }: PaperUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<UploadingFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useUIStore();

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const pdfFiles = Array.from(files).filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (pdfFiles.length === 0) {
      showToast("Only academic PDF documents (.pdf) are supported.", "error");
      return;
    }

    const newItems: UploadingFile[] = pdfFiles.map((file) => ({
      file,
      progress: 0,
      status: "uploading",
    }));

    setUploadQueue((prev) => [...prev, ...newItems]);

    // Process uploads sequentially or concurrently
    for (const item of newItems) {
      try {
        await uploadPaperPdf(item.file, (percent) => {
          setUploadQueue((prev) =>
            prev.map((q) =>
              q.file === item.file ? { ...q, progress: percent } : q
            )
          );
        });

        setUploadQueue((prev) =>
          prev.map((q) =>
            q.file === item.file ? { ...q, progress: 100, status: "success" } : q
          )
        );
        showToast(`Successfully ingested "${item.file.name}"`, "success");
        onUploadSuccess();
      } catch (err: any) {
        setUploadQueue((prev) =>
          prev.map((q) =>
            q.file === item.file
              ? { ...q, status: "error", errorMessage: err.message }
              : q
          )
        );
        showToast(`Failed to upload ${item.file.name}: ${err.message}`, "error");
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="space-y-4">
      {/* Drag & Drop Canvas */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed p-8 text-center cursor-pointer transition-colors bg-parchment-container-lowest dark:bg-darkpaper-container-low ${
          isDragOver
            ? "border-parchment-primary bg-parchment-secondary-container/20"
            : "border-parchment-outline-variant hover:border-parchment-outline"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />

        <FileUp className="w-10 h-10 text-parchment-secondary mx-auto mb-3 opacity-80" />
        <h4 className="font-serif text-base font-medium text-parchment-on-surface dark:text-darkpaper-on-surface mb-1">
          Select or Drag & Drop Academic Research PDFs
        </h4>
        <p className="font-serif text-xs text-parchment-on-surface-variant max-w-md mx-auto leading-relaxed">
          The ingestion pipeline extracts layout text, computes section metadata, generates 384-dimensional pgvector embeddings, and prepares entity graphs.
        </p>

        <div className="mt-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-parchment-primary text-parchment-on-primary text-xs font-serif tracking-wide dark:bg-darkpaper-primary dark:text-darkpaper-on-primary">
            <Upload className="w-3.5 h-3.5" />
            <span>Browse PDF Files</span>
          </span>
        </div>
      </div>

      {/* Upload Progress Queue */}
      {uploadQueue.length > 0 && (
        <div className="space-y-2 border border-parchment-outline-variant p-3 bg-parchment-container-low/50">
          <div className="flex items-center justify-between text-[11px] font-mono tracking-label uppercase text-parchment-secondary">
            <span>Upload & Ingestion Pipeline</span>
            <button
              onClick={() => setUploadQueue([])}
              className="hover:text-parchment-primary text-[10px]"
            >
              Clear Finished
            </button>
          </div>

          {uploadQueue.map((item, idx) => (
            <div
              key={idx}
              className="p-2 border border-parchment-outline-variant/60 bg-parchment-container-lowest text-xs font-serif"
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-medium text-parchment-on-surface truncate">
                  {item.file.name}
                </span>
                <span className="font-mono text-[10px] text-parchment-secondary flex items-center gap-1">
                  {item.status === "success" && (
                    <span className="text-emerald-700 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" /> Indexed
                    </span>
                  )}
                  {item.status === "error" && (
                    <span className="text-rose-700 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> Failed
                    </span>
                  )}
                  {item.status === "uploading" && <span>{item.progress}%</span>}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-parchment-container h-1.5 overflow-hidden">
                <div
                  className={`h-full transition-all duration-200 ${
                    item.status === "error"
                      ? "bg-rose-500"
                      : item.status === "success"
                      ? "bg-emerald-600"
                      : "bg-parchment-primary"
                  }`}
                  style={{ width: `${item.progress}%` }}
                />
              </div>

              {item.errorMessage && (
                <div className="text-[11px] text-rose-600 mt-1 font-serif">
                  {item.errorMessage}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

