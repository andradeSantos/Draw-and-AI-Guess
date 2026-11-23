"use client";

import { useCallback, useEffect, useState } from "react";
import { DrawingCanvas } from "@/components/DrawingCanvas";
import { MuseumChat } from "@/components/MuseumChat";
import { MuseumDashboard } from "@/components/MuseumDashboard";
import { PredictionResult } from "@/components/PredictionResult";
import {
  ApiError,
  getClasses,
  getHealth,
  getStats,
  predictDrawing,
  submitFeedback,
} from "@/lib/api";
import type {
  ClassInfo,
  HealthResponse,
  PredictResponse,
  StatsResponse,
} from "@/lib/types";

type ActiveTab = "visitor" | "museum";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("visitor");

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [classes, setClasses] = useState<ClassInfo[]>([]);

  const [predictResult, setPredictResult] = useState<PredictResponse | null>(null);
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);

  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [healthData, classesData] = await Promise.all([
          getHealth(),
          getClasses(),
        ]);
        setHealth(healthData);
        setClasses(classesData.classes);
      } catch {
        setHealth(null);
      }
    })();
  }, []);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    setStatsError(null);
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      setStatsError(
        err instanceof Error ? err.message : "Erro ao carregar estatísticas."
      );
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "museum") {
      void loadStats();
    }
  }, [activeTab, loadStats]);

  const handlePredict = async (imageBase64: string) => {
    setPredictLoading(true);
    setPredictError(null);
    setFeedbackSubmitted(false);
    setFeedbackMessage(null);

    try {
      const res = await predictDrawing(imageBase64);
      setPredictResult(res);
    } catch (err) {
      setPredictResult(null);
      setPredictError(
        err instanceof Error ? err.message : "Falha ao enviar desenho."
      );
    } finally {
      setPredictLoading(false);
    }
  };

  const handleFeedback = async (isCorrect: boolean, actualClass?: string | null) => {
    if (!predictResult || feedbackSubmitted) return;
    setFeedbackLoading(true);
    try {
      await submitFeedback({
        prediction_id: predictResult.prediction_id,
        is_correct: isCorrect,
        actual_class: actualClass ?? null,
      });
      setFeedbackSubmitted(true);
      setFeedbackMessage("Feedback salvo no PostgreSQL. Obrigado por ajudar a IA!");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFeedbackSubmitted(true);
        setFeedbackMessage("Este desenho já recebeu feedback anteriormente.");
      } else {
        setFeedbackMessage(
          err instanceof Error ? err.message : "Erro ao registrar feedback."
        );
      }
    } finally {
      setFeedbackLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6 sm:px-6">
      <header className="mb-6 flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">🏛️</span>
            <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">
              Museu Ciência Viva — Desenhe e a IA Adivinha
            </h1>
          </div>
          <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                health?.status === "ok" ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
            {health?.status === "ok"
              ? `API Local Conectada · Modelo ${health.model_version} (100% CPU)`
              : "Aguardando conexão com FastAPI em localhost:8000"}
          </p>
        </div>

        <nav className="flex rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setActiveTab("visitor")}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              activeTab === "visitor"
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            🎨 Visitante (Desenhar)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("museum")}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              activeTab === "museum"
                ? "bg-white text-indigo-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            📊 Equipe do Museu
          </button>
        </nav>
      </header>

      {activeTab === "visitor" ? (
        <main className="flex flex-col gap-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <DrawingCanvas
              isLoading={predictLoading}
              onPredict={handlePredict}
              onClearResult={() => {
                setPredictResult(null);
                setPredictError(null);
                setFeedbackSubmitted(false);
                setFeedbackMessage(null);
              }}
            />
            <PredictionResult
              result={predictResult}
              classes={classes}
              isLoading={predictLoading}
              error={predictError}
              feedbackSubmitted={feedbackSubmitted}
              feedbackLoading={feedbackLoading}
              feedbackMessage={feedbackMessage}
              onSubmitFeedback={handleFeedback}
            />
          </div>

          {classes.length > 0 && (
            <section className="rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                O que a IA sabe reconhecer ({classes.length} classes)
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {classes.map((cls) => (
                  <span
                    key={cls.label}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700"
                  >
                    {cls.display_pt}
                  </span>
                ))}
              </div>
            </section>
          )}
        </main>
      ) : (
        <main className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <MuseumDashboard
              stats={stats}
              classes={classes}
              isLoading={statsLoading}
              error={statsError}
              onRefresh={loadStats}
            />
          </div>
          <div className="lg:col-span-2">
            <MuseumChat />
          </div>
        </main>
      )}
    </div>
  );
}
