"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface DrawingCanvasProps {
  isLoading: boolean;
  onPredict: (imageBase64: string) => void;
  onClearResult: () => void;
}

const CANVAS_SIZE = 360;

export function DrawingCanvas({
  isLoading,
  onPredict,
  onClearResult,
}: DrawingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isDrawingRef = useRef(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const historyRef = useRef<ImageData[]>([]);

  const [brushSize, setBrushSize] = useState<number>(12);
  const [hasStrokes, setHasStrokes] = useState<boolean>(false);
  const [canUndo, setCanUndo] = useState<boolean>(false);

  const fillWhiteBackground = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
  }, []);

  useEffect(() => {
    fillWhiteBackground();
  }, [fillWhiteBackground]);

  const getCanvasPoint = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = CANVAS_SIZE / rect.width;
    const scaleY = CANVAS_SIZE / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (isLoading) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.setPointerCapture(e.pointerId);

    // Salva snapshot antes de iniciar o novo traço para suportar Desfazer
    historyRef.current.push(ctx.getImageData(0, 0, CANVAS_SIZE, CANVAS_SIZE));
    if (historyRef.current.length > 20) {
      historyRef.current.shift();
    }
    setCanUndo(true);

    const pt = getCanvasPoint(e);
    isDrawingRef.current = true;
    lastPointRef.current = pt;

    ctx.fillStyle = "#000000";
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, brushSize / 2, 0, Math.PI * 2);
    ctx.fill();
    setHasStrokes(true);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current || isLoading) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx || !lastPointRef.current) return;

    const pt = getCanvasPoint(e);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = brushSize;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    ctx.beginPath();
    ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
    ctx.lineTo(pt.x, pt.y);
    ctx.stroke();

    lastPointRef.current = pt;
  };

  const finishStroke = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;
    lastPointRef.current = null;
    const canvas = canvasRef.current;
    if (canvas && canvas.hasPointerCapture(e.pointerId)) {
      canvas.releasePointerCapture(e.pointerId);
    }
  };

  const handleUndo = () => {
    const canvas = canvasRef.current;
    if (!canvas || historyRef.current.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const prev = historyRef.current.pop();
    if (prev) {
      ctx.putImageData(prev, 0, 0);
    }
    setCanUndo(historyRef.current.length > 0);
    setHasStrokes(historyRef.current.length > 0);
  };

  const handleClear = () => {
    historyRef.current = [];
    setCanUndo(false);
    setHasStrokes(false);
    fillWhiteBackground();
    onClearResult();
  };

  const handleSubmit = () => {
    const canvas = canvasRef.current;
    if (!canvas || isLoading) return;
    const dataUrl = canvas.toDataURL("image/png");
    onPredict(dataUrl);
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Área de Desenho</h2>
          <p className="text-sm text-slate-500">
            Desenhe um dígito (0–9) ou símbolo com o mouse ou dedo.
          </p>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-600">
          <span>Traço:</span>
          <input
            type="range"
            min={6}
            max={20}
            step={2}
            value={brushSize}
            onChange={(e) => setBrushSize(Number(e.target.value))}
            className="w-24 accent-indigo-600"
            aria-label="Espessura do traço"
          />
          <span className="w-8 text-right font-mono text-xs">{brushSize}px</span>
        </label>
      </div>

      <div className="flex justify-center">
        <canvas
          ref={canvasRef}
          width={CANVAS_SIZE}
          height={CANVAS_SIZE}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={finishStroke}
          onPointerCancel={finishStroke}
          className="aspect-square w-full max-w-[360px] cursor-crosshair rounded-xl border-2 border-dashed border-slate-300 bg-white shadow-inner touch-none"
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <button
          type="button"
          onClick={handleUndo}
          disabled={!canUndo || isLoading}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Desfazer
        </button>

        <button
          type="button"
          onClick={handleClear}
          disabled={isLoading}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Limpar
        </button>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={isLoading}
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? "Analisando..." : hasStrokes ? "Adivinhar" : "Enviar"}
        </button>
      </div>
    </div>
  );
}
