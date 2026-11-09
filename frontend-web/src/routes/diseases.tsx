import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ChevronRight, Search } from "lucide-react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-state";
import { ErrorBox, PageTitle, Thinking } from "@/components/shared";

export const Route = createFileRoute("/diseases")({
  head: () => ({
    meta: [
      { title: "Disease Directory — Odisha Public Health Assistant" },
      { name: "description", content: "Browse common diseases and tap one to learn about its symptoms." },
      { property: "og:title", content: "Disease Directory — Odisha Health" },
      { property: "og:description", content: "Browse diseases and ask about symptoms in your language." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: DiseasesPage,
});

function DiseasesPage() {
  const { t } = useApp();
  const [list, setList] = useState<string[] | null>(null);
  const [error, setError] = useState(false);
  const [q, setQ] = useState("");

  const load = () => {
    setError(false); setList(null);
    api.diseases().then((r) => setList(r.diseases)).catch(() => setError(true));
  };
  useEffect(load, []);

  const filtered = list?.filter((d) => d.toLowerCase().includes(q.toLowerCase())) ?? [];

  return (
    <div className="mx-auto w-full max-w-2xl px-3 py-5">
      <PageTitle sub={t.diseasesIntro}>{t.diseases}</PageTitle>
      <label className="relative mb-4 block">
        <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" aria-hidden />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.search} aria-label={t.search}
          className="min-h-12 w-full rounded-xl border-2 border-input bg-card pl-12 pr-4 outline-none focus:border-primary" />
      </label>
      {error && <ErrorBox onRetry={load} />}
      {!list && !error && <Thinking label={t.thinking} />}
      <ul className="divide-y overflow-hidden rounded-2xl border bg-card">
        {filtered.map((d) => (
          <li key={d}>
            <Link to="/" search={{ q: t.askSymptoms(d) }} className="flex min-h-14 items-center justify-between px-4 font-medium capitalize hover:bg-secondary">
              {d}<ChevronRight className="h-5 w-5 text-muted-foreground" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
