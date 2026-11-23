"use client";

import { useEffect, useState } from "react";
import type { ClassInfo, PredictResponse } from "@/lib/types";

interface PredictionResultProps {
  result: PredictResponse | null;
  classes: ClassInfo[];
  isLoading: boolean;
  error: string | null;
  feedbackSubmitted: boolean;
  feedbackLoading: boolean;
  feedbackMessage: string | null;
  onSubmitFeedback: (isCorrect: boolean, actualClass?: string | null) => void;
}

const CLASS_ICONS: Record<string, string> = {
  star: "⭐",
  house: "🏠",
  circle: "⭕",
  triangle: "🔺",
  square: "🟦",
  heart: "❤️",
  cloud: "☁️",
  tree: "🌳",
};

function getClassIcon(label: string): string {
  if (label.startsWith("digit_")) {
    return "🔢";
  }
  return CLASS_ICONS[label] ?? "🎨";
}

function formatUnknownReason(reason: string | null): string {
  if (reason === "blank_canvas") {
    return "O quadro parece estar em branco. Faça um traço antes de enviar.";
  }
  if (reason === "low_margin") {
    return "O desenho ficou muito parecido com mais de uma classe ao mesmo tempo.";
  }
  return "O desenho ficou ambíguo ou parece um rabisco fora das 18 classes treinadas.";
}

export function PredictionResult({
  result,
  classes,
  isLoading,
  error,
  feedbackSubmitted,
  feedbackLoading,
  feedbackMessage,
  onSubmitFeedback,
}: PredictionResultProps) {
  const [showCorrectionPicker, setShowCorrectionPicker] = useState(false);

  useEffect(() => {
    setShowCorrectionPicker(false);
  }, [result?.prediction_id]);

  if (isLoading) {
    return (
      <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
        <p className="text-base font-medium text-slate-700">
          Consultando a rede neural local (CPU)...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[320px] flex-col justify-center gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-rose-800">Erro de Conexão</h3>
        <p className="text-sm text-rose-700">{error}</p>
        <p className="text-xs text-rose-600">
          Verifique se o backend FastAPI está ativo em{" "}
          <code className="font-mono">http://localhost:8000</code>.
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex min-h-[320px] flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 p-6 text-center">
        <span className="text-4xl">🎨</span>
        <h3 className="text-lg font-semibold text-slate-800">
          Pronto para adivinhar!
        </h3>
        <p className="max-w-sm text-sm text-slate-500">
          Desenhe um dos 18 itens no quadro ao lado e clique em{" "}
          <strong>Adivinhar</strong> para ver o palpite da IA e seu nível de
          confiança.
        </p>
      </div>
    );
  }

  const confidencePct = Math.round(result.confidence * 100);
  const marginPct = Math.round(result.margin * 100);
  const isBlank = result.reason === "blank_canvas";

  return (
    <div className="flex flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      {result.is_unknown ? (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🤔</span>
            <div>
              <span className="inline-block rounded-full bg-amber-200 px-2.5 py-0.5 text-xs font-semibold text-amber-900">
                Incerteza Detectada
              </span>
              <h3 className="mt-1 text-2xl font-bold text-amber-950">Não sei</h3>
            </div>
          </div>
          <p className="mt-2 text-sm text-amber-900">
            {formatUnknownReason(result.reason)}
          </p>
          {!isBlank && (
            <p className="mt-2 font-mono text-xs text-amber-800">
              Confiança máx: {confidencePct}% · Margem top-1/top-2: {marginPct}% ·{" "}
              {result.latency_ms.toFixed(1)} ms
            </p>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-4xl">{getClassIcon(result.predicted_class)}</span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  Palpite da IA
                </p>
                <h3 className="text-3xl font-bold text-slate-900">
                  {result.display_name}
                </h3>
              </div>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-emerald-700">
                {confidencePct}%
              </span>
              <p className="font-mono text-xs text-slate-500">
                {result.latency_ms.toFixed(1)} ms
              </p>
            </div>
          </div>

          <div className="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-emerald-100">
            <div
              className="h-full rounded-full bg-emerald-600 transition-all duration-300"
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>
      )}

      {result.top_k.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Top-3 Probabilidades
          </h4>
          <div className="flex flex-col gap-1.5">
            {result.top_k.map((item) => {
              const pct = Math.round(item.confidence * 100);
              return (
                <div
                  key={item.label}
                  className="flex items-center gap-3 text-sm"
                >
                  <span className="w-24 truncate font-medium text-slate-700">
                    {item.display_name}
                  </span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-indigo-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="w-10 text-right font-mono text-xs text-slate-600">
                    {pct}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!isBlank && (
        <div className="border-t border-slate-200 pt-4">
          <h4 className="text-sm font-semibold text-slate-800">
            {result.is_unknown
              ? "O que você tentou desenhar?"
              : "A IA acertou seu desenho?"}
          </h4>

          {feedbackSubmitted ? (
            <div className="mt-2 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-800">
              {feedbackMessage ?? "Feedback registrado no PostgreSQL. Obrigado!"}
            </div>
          ) : (
            <div className="mt-3 flex flex-col gap-3">
              {!result.is_unknown && (
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    disabled={feedbackLoading}
                    onClick={() => onSubmitFeedback(true, null)}
                    className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50"
                  >
                    ✓ Acertou
                  </button>
                  <button
                    type="button"
                    disabled={feedbackLoading}
                    onClick={() => setShowCorrectionPicker(true)}
                    className="rounded-xl border border-rose-300 bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:opacity-50"
                  >
                    ✕ Errou
                  </button>
                </div>
              )}

              {(showCorrectionPicker || result.is_unknown) && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <p className="mb-2 text-xs font-medium text-slate-600">
                    Selecione a classe correta (ou confirme que era apenas um rabisco):
                  </p>
                  <div className="grid grid-cols-3 gap-1.5 sm:grid-cols-6">
                    {classes.map((cls) => (
                      <button
                        key={cls.label}
                        type="button"
                        disabled={feedbackLoading}
                        onClick={() => onSubmitFeedback(false, cls.label)}
                        className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs font-medium text-slate-700 transition hover:border-indigo-400 hover:bg-indigo-50 disabled:opacity-50"
                      >
                        {cls.display_pt}
                      </button>
                    ))}
                  </div>
                  {result.is_unknown && (
                    <button
                      type="button"
                      disabled={feedbackLoading}
                      onClick={() => onSubmitFeedback(true, null)}
                      className="mt-2 w-full rounded-lg border border-amber-300 bg-amber-100/70 px-3 py-1.5 text-xs font-semibold text-amber-900 transition hover:bg-amber-200/70 disabled:opacity-50"
                    >
                      Era mesmo um rabisco / fora das classes (IA acertou em dizer &quot;Não sei&quot;)
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
