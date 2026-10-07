import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import he from "./he.json";

export type Lang = "he" | "en";
const dirOf = (l: string) => (l === "he" ? "rtl" : "ltr");

function apply(lng: string) {
  document.documentElement.lang = lng;
  document.documentElement.dir = dirOf(lng);
  try { localStorage.setItem("lang", lng); } catch { /* storage unavailable */ }
}

let saved: string | null = null;
try { saved = localStorage.getItem("lang"); } catch { /* storage unavailable */ }

i18n.use(initReactI18next).init({
  resources: { he: { translation: he }, en: { translation: en } },
  lng: saved === "en" ? "en" : "he", // Hebrew is the default
  fallbackLng: "he",
  interpolation: { escapeValue: false },
});
i18n.on("languageChanged", apply);
apply(i18n.language);

export default i18n;
