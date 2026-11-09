<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Backend URL lives only in src/lib/api.ts (API_BASE_URL, overridable via VITE_API_BASE_URL) — single place to repoint at a deployed FastAPI.
- Language, text size, contrast and chat history live in src/lib/app-state.tsx context so they persist across pages.
