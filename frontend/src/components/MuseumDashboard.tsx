"use client";

import type { ClassInfo, StatsResponse } from "@/lib/types";

interface MuseumDashboardProps {
  stats: StatsResponse | null;
  classes: ClassInfo[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export function MuseumDashboard({
  stats,
  classes,
  isLoading,
  error,
  onRefresh,
}: MuseumDashboardProps) {
  const displayName = (label: string) => {
    if (label === "Não sei") return "Não sei";
    return classes.find((c) => c.label === label)?.display_pt ?? label;
  };

  return (
    <div className="flex flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Dashboard da Exposição
          </h2>
          <p className="text-sm text-slate-500">
            Métricas reais agregadas do PostgreSQL local.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          className="rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
        >
          {isLoading ? "Atualizando..." : "↻ Atualizar"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {stats && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5">
              <p className="text-xs font-medium text-slate-500">Total de Desenhos</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {stats.total_predictions}
              </p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-3.5">
              <p className="text-xs font-medium text-emerald-700">Taxa de Acerto</p>
              <p className="mt-1 text-2xl font-bold text-emerald-900">
                {stats.accuracy_rate !== null
                  ? `${Math.round(stats.accuracy_rate * 1000) / 10}%`
                  : "—"}
              </p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3.5">
              <p className="text-xs font-medium text-amber-800">&quot;Não sei&quot;</p>
              <p className="mt-1 text-2xl font-bold text-amber-950">
                {stats.unknown_count}{" "}
                <span className="text-xs font-normal">
                  ({Math.round(stats.unknown_rate * 1000) / 10}%)
                </span>
              </p>
            </div>
            <div className="rounded-xl border border-indigo-200 bg-indigo-50/70 p-3.5">
              <p className="text-xs font-medium text-indigo-700">Feedbacks</p>
              <p className="mt-1 text-2xl font-bold text-indigo-950">
                {stats.feedback_count}
              </p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-800">
                Pares Mais Confundidos
              </h3>
              {stats.top_confusions.length === 0 ? (
                <p className="text-xs text-slate-500">
                  Ainda não há erros com classe real informada pelos visitantes.
                </p>
              ) : (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th className="pb-2 font-medium">IA previu</th>
                      <th className="pb-2 font-medium">Real</th>
                      <th className="pb-2 text-right font-medium">Qtd</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {stats.top_confusions.map((pair, idx) => (
                      <tr key={`${pair.predicted_class}-${pair.actual_class}-${idx}`}>
                        <td className="py-2 font-medium text-slate-700">
                          {displayName(pair.predicted_class)}
                        </td>
                        <td className="py-2 font-medium text-indigo-700">
                          {displayName(pair.actual_class)}
                        </td>
                        <td className="py-2 text-right font-mono text-slate-600">
                          {pair.count}x
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-800">
                Distribuição por Classe
              </h3>
              {stats.class_distribution.length === 0 ? (
                <p className="text-xs text-slate-500">
                  Nenhum desenho registrado ainda.
                </p>
              ) : (
                <div className="flex max-h-48 flex-col gap-2 overflow-y-auto pr-1">
                  {stats.class_distribution.map((item) => {
                    const pct =
                      stats.total_predictions > 0
                        ? Math.round((item.count / stats.total_predictions) * 100)
                        : 0;
                    return (
                      <div
                        key={item.predicted_class}
                        className="flex items-center gap-2 text-xs"
                      >
                        <span className="w-24 truncate font-medium text-slate-700">
                          {displayName(item.predicted_class)}
                        </span>
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-indigo-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="w-10 text-right font-mono text-slate-600">
                          {item.count}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
