import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Check, ShieldAlert, ShieldCheck, Shield } from "lucide-react";
import { api, type RiskResponse } from "@/lib/api";
import { useApp } from "@/lib/app-state";
import { Disclaimer, ErrorBox, PageTitle, Thinking } from "@/components/shared";

export const Route = createFileRoute("/risk")({
  head: () => ({
    meta: [
      { title: "Symptom Risk Check — Odisha Public Health Assistant" },
      { name: "description", content: "A short step-by-step check of your symptoms with a clear low, moderate or high risk result." },
      { property: "og:title", content: "Symptom Risk Check — Odisha Health" },
      { property: "og:description", content: "Answer a few questions to understand your health risk level." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: RiskPage,
});

const AGES = ["0-5", "6-17", "18-40", "41-60", "60+"];
const SYMPTOMS = ["fever", "cough", "headache", "body ache", "vomiting", "diarrhea", "rash", "breathing difficulty", "chest pain", "chills", "fatigue", "bleeding", "confusion", "sore throat"];
const CONDITIONS = ["diabetes", "hypertension", "heart disease", "asthma", "kidney disease", "HIV", "cancer"];

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" aria-pressed={on} onClick={onClick}
      className={`inline-flex min-h-12 items-center gap-1.5 rounded-full border-2 px-4 font-medium capitalize ${on ? "border-primary bg-primary text-primary-foreground" : "border-input bg-card"}`}>
      {on && <Check className="h-4 w-4" />}{children}
    </button>
  );
}

function RiskPage() {
  const { t } = useApp();
  const [step, setStep] = useState(0);
  const [age, setAge] = useState("");
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [days, setDays] = useState("");
  const [temp, setTemp] = useState("");
  const [pregnant, setPregnant] = useState<boolean | null>(null);
  const [conds, setConds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [result, setResult] = useState<RiskResponse | null>(null);

  const toggle = (arr: string[], set: (v: string[]) => void, v: string) =>
    set(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  const submit = async () => {
    setLoading(true); setError(false);
    try {
      setResult(await api.risk({
        age_group: age, symptoms,
        duration_days: days ? Number(days) : undefined,
        temperature_celsius: temp ? Number(temp) : undefined,
        existing_conditions: conds.length ? conds : undefined,
        pregnant: pregnant ?? undefined,
      }));
    } catch { setError(true); } finally { setLoading(false); }
  };

  const reset = () => { setStep(0); setAge(""); setSymptoms([]); setDays(""); setTemp(""); setPregnant(null); setConds([]); setResult(null); setError(false); };

  const total = 4;
  const canNext = [age !== "", symptoms.length > 0, true, true][step];
  const inputCls = "min-h-12 w-full rounded-xl border-2 border-input bg-card px-4 text-lg outline-none focus:border-primary";

  if (result) {
    const s = {
      low: { cls: "border-ok bg-ok-soft", head: "bg-ok", Icon: ShieldCheck, label: t.riskLow },
      moderate: { cls: "border-warn bg-warn-soft", head: "bg-warn", Icon: Shield, label: t.riskModerate },
      high: { cls: "border-emergency bg-emergency-soft", head: "bg-emergency", Icon: ShieldAlert, label: t.riskHigh },
    }[result.risk_level] ?? { cls: "border-neutral bg-neutral-soft", head: "bg-neutral", Icon: Shield, label: result.risk_level };
    return (
      <div className="mx-auto w-full max-w-2xl px-3 py-5">
        <div role="status" className={`overflow-hidden rounded-2xl border-4 ${s.cls}`}>
          <div className={`flex items-center gap-3 px-5 py-4 text-primary-foreground ${s.head}`}>
            <s.Icon className="h-8 w-8" aria-hidden />
            <span className="text-2xl font-bold">{s.label}</span>
          </div>
          <div className="space-y-4 p-5">
            <div>
              <h2 className="mb-1 font-semibold">{t.recommendation}</h2>
              <p className="text-lg leading-relaxed">{result.recommendation}</p>
            </div>
            {result.factors_considered?.length > 0 && (
              <div>
                <h2 className="mb-1 font-semibold">{t.factors}</h2>
                <ul className="list-disc space-y-1 pl-5">{result.factors_considered.map((f, i) => <li key={i}>{f}</li>)}</ul>
              </div>
            )}
            <Disclaimer text={result.disclaimer} />
          </div>
        </div>
        <button onClick={reset} className="mt-4 min-h-12 w-full rounded-xl border-2 border-primary font-semibold text-primary">{t.startOver}</button>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-3 py-5">
      <PageTitle>{t.risk}</PageTitle>
      <div className="mb-4">
        <p className="mb-2 text-sm text-muted-foreground">{t.step} {step + 1} {t.of} {total}</p>
        <div className="flex gap-1.5">{Array.from({ length: total }).map((_, i) => <div key={i} className={`h-2 flex-1 rounded-full ${i <= step ? "bg-primary" : "bg-muted"}`} />)}</div>
      </div>
      <div className="rounded-2xl border bg-card p-5">
        {step === 0 && (<fieldset><legend className="mb-3 text-lg font-semibold">{t.ageGroup}</legend>
          <div className="flex flex-wrap gap-2">{AGES.map((a) => <Chip key={a} on={age === a} onClick={() => setAge(a)}>{a}</Chip>)}</div></fieldset>)}
        {step === 1 && (<fieldset><legend className="mb-3 text-lg font-semibold">{t.symptoms}</legend>
          <div className="flex flex-wrap gap-2">{SYMPTOMS.map((s) => <Chip key={s} on={symptoms.includes(s)} onClick={() => toggle(symptoms, setSymptoms, s)}>{s}</Chip>)}</div></fieldset>)}
        {step === 2 && (<div className="space-y-4">
          <label className="block"><span className="mb-1.5 block text-lg font-semibold">{t.duration}</span>
            <input type="number" inputMode="numeric" min={0} max={365} value={days} onChange={(e) => setDays(e.target.value)} className={inputCls} /></label>
          <label className="block"><span className="mb-1.5 block text-lg font-semibold">{t.temp}</span>
            <input type="number" inputMode="decimal" step="0.1" min={30} max={45} placeholder="37.0" value={temp} onChange={(e) => setTemp(e.target.value)} className={inputCls} /></label>
        </div>)}
        {step === 3 && (<div className="space-y-5">
          <fieldset><legend className="mb-3 text-lg font-semibold">{t.pregnant}</legend>
            <div className="flex gap-2"><Chip on={pregnant === true} onClick={() => setPregnant(true)}>{t.yes}</Chip><Chip on={pregnant === false} onClick={() => setPregnant(false)}>{t.no}</Chip></div></fieldset>
          <fieldset><legend className="mb-3 text-lg font-semibold">{t.conditions}</legend>
            <div className="flex flex-wrap gap-2">{CONDITIONS.map((c) => <Chip key={c} on={conds.includes(c)} onClick={() => toggle(conds, setConds, c)}>{c}</Chip>)}</div></fieldset>
        </div>)}
      </div>
      <div className="mt-4 space-y-3">
        {loading && <Thinking label={t.thinking} />}
        {error && <ErrorBox onRetry={submit} />}
        <div className="flex gap-2">
          {step > 0 && <button onClick={() => setStep(step - 1)} disabled={loading} className="min-h-12 flex-1 rounded-xl border-2 font-semibold">{t.back}</button>}
          {step < total - 1
            ? <button onClick={() => setStep(step + 1)} disabled={!canNext} className="min-h-12 flex-[2] rounded-xl bg-primary font-semibold text-primary-foreground disabled:opacity-40">{t.next}</button>
            : <button onClick={submit} disabled={loading} className="min-h-12 flex-[2] rounded-xl bg-primary font-semibold text-primary-foreground disabled:opacity-40">{t.check}</button>}
        </div>
      </div>
    </div>
  );
}
