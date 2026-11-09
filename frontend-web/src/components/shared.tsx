import { ExternalLink, WifiOff, RotateCcw } from "lucide-react";
import type { Source } from "@/lib/api";
import { useApp } from "@/lib/app-state";

export function Thinking({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3 text-muted-foreground">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span key={i} className="typing-dot h-2.5 w-2.5 rounded-full bg-primary" style={{ animationDelay: `${i * 0.15}s` }} />
        ))}
      </span>
      <span>{label}</span>
    </div>
  );
}

export function ErrorBox({ onRetry }: { onRetry?: () => void }) {
  const { t } = useApp();
  return (
    <div role="alert" className="flex flex-col gap-3 rounded-xl border-2 border-alert bg-alert-soft p-4 sm:flex-row sm:items-center">
      <WifiOff className="h-6 w-6 shrink-0 text-alert" aria-hidden />
      <p className="flex-1">{t.errUnreachable}</p>
      {onRetry && (
        <button onClick={onRetry} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 font-semibold text-primary-foreground">
          <RotateCcw className="h-4 w-4" />{t.retry}
        </button>
      )}
    </div>
  );
}

export function SourceList({ sources }: { sources: Source[] }) {
  const { t } = useApp();
  if (!sources?.length) return null;
  return (
    <div className="mt-3 border-t pt-3">
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t.sources}</p>
      <ul className="space-y-1.5">
        {sources.map((s, i) => (
          <li key={i}>
            <a href={s.url} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-start gap-1.5 text-sm font-medium text-primary underline underline-offset-2">
              <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              <span>{s.source}{s.publisher ? ` — ${s.publisher}` : ""}{s.publication_date ? ` (${s.publication_date})` : ""}</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Disclaimer({ text }: { text: string }) {
  if (!text) return null;
  return <p className="mt-2 text-xs leading-snug text-muted-foreground">ⓘ {text}</p>;
}

export function PageTitle({ children, sub }: { children: React.ReactNode; sub?: string }) {
  return (
    <div className="mb-4">
      <h1 className="font-display text-2xl font-semibold">{children}</h1>
      {sub && <p className="mt-1 text-muted-foreground">{sub}</p>}
    </div>
  );
}
