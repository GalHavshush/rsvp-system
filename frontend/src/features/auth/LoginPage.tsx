import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, errorCode } from "../../api/client";
import { LanguageSwitcher } from "../../components/LanguageSwitcher";

export function LoginPage({ setup }: { setup: boolean }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const submit = useMutation({
    mutationFn: async () => {
      const body = { email, password };
      const r = setup ? await api.POST("/api/auth/setup", { body }) : await api.POST("/api/auth/login", { body });
      if (r.error) throw new Error(errorCode(r.error));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth"] }),
  });
  const onSubmit = (e: FormEvent) => { e.preventDefault(); submit.mutate(); };
  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-4 px-4">
      <div className="flex justify-between">
        <h1 className="text-2xl font-semibold">{setup ? t("auth.setupTitle") : t("auth.loginTitle")}</h1>
        <LanguageSwitcher />
      </div>
      {setup && <p className="text-stone-600">{t("auth.setupHint")}</p>}
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <input dir="ltr" type="email" required autoComplete="username" placeholder={t("auth.email")} value={email}
          onChange={(e) => setEmail(e.target.value)} className="rounded-lg border border-stone-300 bg-white px-3 py-2" />
        <input dir="ltr" type="password" required minLength={8} autoComplete={setup ? "new-password" : "current-password"}
          placeholder={t("auth.password")} value={password} onChange={(e) => setPassword(e.target.value)}
          className="rounded-lg border border-stone-300 bg-white px-3 py-2" />
        {submit.error && <p role="alert" className="text-sm text-red-700">{t(`errors.${submit.error.message}`, t("errors.generic"))}</p>}
        <button disabled={submit.isPending} className="rounded-lg bg-stone-900 px-4 py-2 text-white disabled:opacity-50">
          {setup ? t("auth.setupSubmit") : t("auth.loginSubmit")}
        </button>
      </form>
    </main>
  );
}
