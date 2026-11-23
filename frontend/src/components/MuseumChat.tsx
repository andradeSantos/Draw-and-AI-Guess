"use client";

import { useState } from "react";
import { sendChatMessage } from "@/lib/api";

interface ChatMessage {
  id: string;
  sender: "operator" | "bot";
  text: string;
}

const QUICK_PROMPTS = [
  { label: "Resumo (/stats)", query: "/stats" },
  { label: "Quantos desenhos?", query: "Quantos desenhos foram feitos?" },
  { label: "Taxa de acerto", query: "Qual a taxa de acerto?" },
  { label: "O que a IA mais confunde?", query: "O que a IA mais confunde?" },
  { label: "Ajuda (/help)", query: "/help" },
];

export function MuseumChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "bot",
      text: "Olá, equipe do Museu Ciência Viva! Pergunte sobre o total de desenhos, taxa de acerto ou classes mais confundidas.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || sending) return;

    const operatorMsg: ChatMessage = {
      id: `op-${Date.now()}`,
      sender: "operator",
      text: trimmed,
    };
    setMessages((prev) => [...prev, operatorMsg]);
    setInput("");
    setSending(true);

    try {
      const response = await sendChatMessage(trimmed);
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-${Date.now()}`,
          sender: "bot",
          text: response.reply,
        },
      ]);
    } catch (err) {
      const errText =
        err instanceof Error ? err.message : "Erro ao consultar o chat da API.";
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "bot",
          text: `Não foi possível obter resposta: ${errText}`,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">
          Simulador de Chat da Equipe
        </h2>
        <p className="text-sm text-slate-500">
          Consultas 100% locais sobre as estatísticas do PostgreSQL.
        </p>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {QUICK_PROMPTS.map((chip) => (
          <button
            key={chip.label}
            type="button"
            disabled={sending}
            onClick={() => handleSend(chip.query)}
            className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 transition hover:bg-indigo-100 disabled:opacity-50"
          >
            {chip.label}
          </button>
        ))}
      </div>

      <div className="flex min-h-[260px] max-h-[340px] flex-1 flex-col gap-2.5 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
              msg.sender === "operator"
                ? "self-end bg-indigo-600 text-white"
                : "self-start border border-slate-200 bg-white text-slate-800"
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void handleSend(input);
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Digite uma pergunta ou /stats..."
          disabled={sending}
          className="flex-1 rounded-xl border border-slate-300 px-3.5 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
