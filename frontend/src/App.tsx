import { useTranslation } from "react-i18next";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "./features/auth/LoginPage";
import { useAuth } from "./features/auth/useAuth";
import { EventsPage } from "./features/events/EventsPage";
import { AdminLayout } from "./layouts/AdminLayout";

export function App() {
  const { t } = useTranslation();
  const auth = useAuth();
  if (auth.isLoading) return <p className="p-8 text-center text-stone-500">{t("common.loading")}</p>;
  if (!auth.data?.user) return <LoginPage setup={auth.data?.needsSetup ?? false} />;
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AdminLayout />}>
          <Route index element={<EventsPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
