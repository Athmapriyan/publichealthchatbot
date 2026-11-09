import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Mic, SendHorizontal, Siren, Phone } from "lucide-react";
import { api, type ChatResponse } from "@/lib/api";
import { useApp, type ChatMsg } from "@/lib/app-state";
import { Disclaimer, ErrorBox, SourceList, Thinking } from "@/components/shared";

export const Route = createFileRoute("/")({
  validateSearch: (s: Record<string, unknown>): { q?: string | undefined } => ({ q: typeof s["q"] === "string" ? s["q"] : undefined }),
  head: () => ({
    meta: [
      { title: "Ask a Health Question — Odisha Public Health Assistant" },
      { name: "description", content: "Ask trusted health questions in English, Hindi or Odia, with cited official sources." },
      { property: "og:title", content: "Odisha Public Health Assistant" },
      { property: "og:description", content: "Trusted health answers in English, Hindi and Odia from the Government of Odisha." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: ChatPage,
});

const uid = () => Math.random().toString(36).slice(2);

function BotBubble({ data }: { data: ChatResponse }) {
  const { t } = useApp();
  if (data.is_emergency) {
    return (
      <div role="alert" className="overflow-hidden rounded-xl border-4 border-emergency bg-emergency-soft shadow-lg">
        <div className="flex items-center gap-2 bg-emergency px-4 py-3 text-emergency-foreground">
          <Siren className="h-6 w-6" aria-hidden />
          <span className="text-lg font-bold uppercase tracking-wide">{t.emergency}</span>
        </div>
        <div className="p-4">
          <a href="tel:108" className="mb-3 flex min-h-12 items-center justify-center gap-2 rounded-lg bg-emergency px-4 text-lg font-bold text-emergency-foreground">
            <Phone className="h-5 w-5" /> 108
          </a>
          <p className="mb-2 font-semibold">{t.emergencyCall}</p>
          <p className="whitespace-pre-wrap">{data.response}</p>
          <SourceList sources={data.sources} />
          <Disclaimer text={data.disclaimer} />
        </div>
      </div>
    );
  }
  return (
    <div className="max-w-[92%] rounded-2xl rounded-tl-sm border bg-card p-4 shadow-sm">
      <p className="whitespace-pre-wrap leading-relaxed">{data.response}</p>
      <SourceList sources={data.sources} />
      <Disclaimer text={data.disclaimer} />
    </div>
  );
}

function ChatPage() {
  const { t, lang, messages, setMessages, sessionId } = useApp();
  const { q } = Route.useSearch();
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [micTip, setMicTip] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, loading]);

  const send = async (text: string, { addUser = true }: { addUser?: boolean } = {}) => {
    const msg = text.trim();
    if (!msg || loading) return;
    if (addUser) setMessages((m) => [...m, { id: uid(), role: "user", text: msg }]);
    else setMessages((m) => m.filter((x) => !(x.role === "error" && x.retryText === msg)));
    setInput("");
    setLoading(true);
    try {
      const data = await api.chat(msg, lang, sessionId);
      setMessages((m) => [...m, { id: uid(), role: "bot", data }]);
    } catch {
      setMessages((m) => [...m, { id: uid(), role: "error", retryText: msg }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (q) { send(q); navigate({ to: "/", search: { q: undefined }, replace: true }); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
      <div className="flex-1 space-y-4 px-3 py-4" aria-live="polite">
        {messages.length === 0 && (
          <div className="rounded-2xl border bg-card p-5">
            <p className="mb-4 text-lg">{t.welcome}</p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {t.suggestions.map((s) => (
                <button key={s} onClick={() => send(s)}
                  className="min-h-12 rounded-xl border-2 border-primary/30 bg-secondary px-4 text-left font-medium text-secondary-foreground hover:border-primary">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m: ChatMsg) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-primary-foreground">{m.text}</p>
            </div>
          ) : m.role === "bot" ? (
            <BotBubble key={m.id} data={m.data} />
          ) : (
            <ErrorBox key={m.id} onRetry={() => send(m.retryText, { addUser: false })} />
          ),
        )}
        {loading && <Thinking label={t.thinking} />}
        <div ref={endRef} />
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(input); }}
        className="sticky bottom-0 border-t bg-background/95 px-3 py-3 backdrop-blur">
        <div className="relative flex items-end gap-2">
          <div className="relative">
            <button type="button" onClick={() => { setMicTip(true); setTimeout(() => setMicTip(false), 2500); }}
              aria-label={t.micSoon} title={t.micSoon}
              className="grid h-12 w-12 place-items-center rounded-full border-2 bg-muted text-muted-foreground">
              <Mic className="h-5 w-5" />
            </button>
            {micTip && (
              <span role="status" className="absolute bottom-14 left-0 whitespace-nowrap rounded-lg bg-foreground px-3 py-2 text-sm text-background shadow">
                {t.micSoon}
              </span>
            )}
          </div>
          <textarea value={input} onChange={(e) => setInput(e.target.value)} rows={1} placeholder={t.placeholder}
            aria-label={t.placeholder}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
            className="max-h-36 min-h-12 flex-1 resize-none rounded-2xl border-2 border-input bg-card px-4 py-3 text-base outline-none focus:border-primary" />
          <button type="submit" disabled={!input.trim() || loading} aria-label={t.send}
            className="grid h-12 w-12 place-items-center rounded-full bg-primary text-primary-foreground disabled:opacity-40">
            <SendHorizontal className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
