import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Desenhe e a IA Adivinha — Museu Ciência Viva",
  description:
    "Atração interativa local com PyTorch CPU, FastAPI, PostgreSQL e Next.js.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-slate-100 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
