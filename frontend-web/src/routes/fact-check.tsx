import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { api, type MisinfoResponse, type Verdict } from "@/lib/api";
import { useApp } from "@/lib/app-state";
import { ErrorBox, PageTitle, SourceList, Thinking } from "@/components/shared";

export const Route = createFileRoute("/fact-check")({
  head: () => ({
    meta: [
      { title: "Health Fact Check — Odisha Public Health Assistant" },
      { name: "description", content: "Paste a forwarded health message to check it against trusted official sources." },
      { property: "og:title", content: "Health Fact Check — Odisha Health" },
      { property: "og:description", content: "Check whether a health claim is true, false or misleading." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: FactPage,
});

const STYLE: Record<Verdict, string> = {
  supported: "bg-ok text-primary-foreground",
  false: "bg-emergency text-emergency-foreground",
  misleading: "bg-alert text-primary-foreground",
  unsupported: "bg-neutral text-primary-foreground",
  insufficient_evidence: "bg-neutral text-primary-foreground",
};

function FactPage() {
  const { t } = useApp();
  const [claim, setClaim] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [res, setRes] = useState<MisinfoResponse | null>(null);

  const check = async () => {
    if (!claim.trim()) return;
    setLoading(true); setError(false); setRes(null);
    try { setRes(await api.misinfo(claim.trim())); } catch { setError(true); } finally { setLoading(false); }
  };

  return (
    <div className="mx-auto w-full max-w-2xl px-3 py-5">
      <PageTitle sub={t.factIntro}>{t.fact}</PageTitle>
      <textarea value={claim} onChange={(e) => setClaim(e.target.value)} rows={6} placeholder={t.factPlaceholder} aria-label={t.factPlaceholder}
        className="w-full rounded-2xl border-2 border-input bg-card p-4 text-base outline-none focus:border-primary" />
      <button onClick={check} disabled={!claim.trim() || loading}
        className="mt-3 min-h-12 w-full rounded-xl bg-primary font-semibold text-primary-foreground disabled:opacity-40">{t.factCheck}</button>
      <div className="mt-4 space-y-3">
        {loading && <Thinking label={t.thinking} />}
        {error && <ErrorBox onRetry={check} />}
        {res && (
          <div role="status" className="rounded-2xl border bg-card p-5">
            <span className={`inline-block rounded-full px-4 py-1.5 text-lg font-bold ${STYLE[res.verdict] ?? STYLE.unsupported}`}>
              {t[`v_${res.verdict}` as `v_${Verdict}`] ?? res.verdict}
            </span>
            <blockquote className="mt-3 border-l-4 pl-3 italic text-muted-foreground">“{res.claim}”</blockquote>
            <h2 className="mt-4 font-semibold">{t.explanation}</h2>
            <p className="mt-1 leading-relaxed">{res.explanation}</p>
            <SourceList sources={res.sources} />
          </div>
        )}
      </div>
    </div>
  );
}
