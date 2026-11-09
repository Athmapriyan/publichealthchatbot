import { Link } from "@tanstack/react-router";
import { MessageCircle, Activity, ShieldCheck, BookOpen, Type, Contrast, Landmark } from "lucide-react";
import { useApp } from "@/lib/app-state";
import type { Lang } from "@/lib/api";

const langs: { code: Lang; label: string }[] = [
  { code: "en", label: "English" }, { code: "hi", label: "हिन्दी" }, { code: "or", label: "ଓଡ଼ିଆ" },
];

export function AppHeader() {
  const { t, lang, setLang, largeText, setLargeText, contrast, setContrast } = useApp();
  const nav = [
    { to: "/", label: t.chat, icon: MessageCircle },
    { to: "/risk", label: t.risk, icon: Activity },
    { to: "/fact-check", label: t.fact, icon: ShieldCheck },
    { to: "/diseases", label: t.diseases, icon: BookOpen },
  ] as const;

  return (
    <header className="sticky top-0 z-20 bg-header text-header-foreground shadow-md">
      <div className="h-1 bg-gold" />
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-3 py-2.5">
        <div aria-label="Government emblem placeholder" className="grid h-11 w-11 shrink-0 place-items-center rounded-full border-2 border-gold/70 bg-header-foreground/10">
          <Landmark className="h-6 w-6 text-gold" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-display text-lg font-semibold leading-tight">{t.title}</p>
          <p className="truncate text-xs opacity-80">{t.dept}</p>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setLargeText(!largeText)} aria-pressed={largeText} title={t.largerText}
            className={`grid h-11 w-11 place-items-center rounded-lg ${largeText ? "bg-header-foreground text-header" : "hover:bg-header-foreground/10"}`}>
            <Type className="h-5 w-5" /><span className="sr-only">{t.largerText}</span>
          </button>
          <button onClick={() => setContrast(!contrast)} aria-pressed={contrast} title={t.contrast}
            className={`grid h-11 w-11 place-items-center rounded-lg ${contrast ? "bg-header-foreground text-header" : "hover:bg-header-foreground/10"}`}>
            <Contrast className="h-5 w-5" /><span className="sr-only">{t.contrast}</span>
          </button>
        </div>
      </div>
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-3 pb-2">
        <div role="radiogroup" aria-label="Language" className="flex rounded-lg bg-header-foreground/10 p-1">
          {langs.map((l) => (
            <button key={l.code} role="radio" aria-checked={lang === l.code} onClick={() => setLang(l.code)}
              className={`min-h-10 rounded-md px-3 text-sm font-medium ${lang === l.code ? "bg-header-foreground text-header" : ""}`}>
              {l.label}
            </button>
          ))}
        </div>
        <span className="text-xs font-semibold text-gold">{t.helplines}</span>
      </div>
      <nav className="border-t border-header-foreground/15 bg-header">
        <div className="mx-auto grid max-w-5xl grid-cols-4">
          {nav.map((n) => (
            <Link key={n.to} to={n.to}
              className="flex min-h-14 flex-col items-center justify-center gap-0.5 border-b-4 border-transparent px-1 text-xs font-medium opacity-80 sm:flex-row sm:gap-2 sm:text-sm"
              activeProps={{ className: "!border-gold !opacity-100" }}
              activeOptions={{ exact: true }}>
              <n.icon className="h-5 w-5" aria-hidden />{n.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
