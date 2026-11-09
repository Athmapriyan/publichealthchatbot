import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { ChatResponse, Lang } from "./api";
import { dict, type Dict } from "./i18n";

export type ChatMsg =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "bot"; data: ChatResponse }
  | { id: string; role: "error"; retryText: string };

interface State {
  lang: Lang; setLang: (l: Lang) => void; t: Dict;
  largeText: boolean; setLargeText: (v: boolean) => void;
  contrast: boolean; setContrast: (v: boolean) => void;
  messages: ChatMsg[]; setMessages: React.Dispatch<React.SetStateAction<ChatMsg[]>>;
  sessionId: string;
}
const Ctx = createContext<State | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [lang, setLangS] = useState<Lang>("en");
  const [largeText, setLargeTextS] = useState(false);
  const [contrast, setContrastS] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2) + Date.now().toString(36));

  useEffect(() => {
    const l = localStorage.getItem("lang") as Lang | null;
    if (l && l in dict) setLangS(l);
    setLargeTextS(localStorage.getItem("lg") === "1");
    setContrastS(localStorage.getItem("hc") === "1");
  }, []);
  useEffect(() => {
    document.documentElement.classList.toggle("lg-text", largeText);
    document.documentElement.classList.toggle("hc", contrast);
    document.documentElement.lang = lang;
  }, [largeText, contrast, lang]);

  const setLang = (l: Lang) => { setLangS(l); localStorage.setItem("lang", l); };
  const setLargeText = (v: boolean) => { setLargeTextS(v); localStorage.setItem("lg", v ? "1" : "0"); };
  const setContrast = (v: boolean) => { setContrastS(v); localStorage.setItem("hc", v ? "1" : "0"); };

  return (
    <Ctx.Provider value={{ lang, setLang, t: dict[lang], largeText, setLargeText, contrast, setContrast, messages, setMessages, sessionId }}>
      {children}
    </Ctx.Provider>
  );
}

export function useApp() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useApp outside provider");
  return c;
}
