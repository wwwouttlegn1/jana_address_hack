
import { MapPin, MapPinned, Database } from "lucide-react";

type Page = "parser" | "dashboard";

interface HeaderProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

export default function Header({
  currentPage,
  onNavigate,
}: HeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-3 text-white">
            <MapPin size={24} />
          </div>

          <div>
            <h1 className="text-xl font-extrabold text-blue-700">
              JANA ADDRESS
            </h1>
            <p className="text-xs text-slate-400">
              Интеллектуальный разбор адресов
            </p>
          </div>
        </div>

        <nav className="flex flex-wrap gap-2">
          <button
            onClick={() => onNavigate("parser")}
            className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition ${
              currentPage === "parser"
                ? "bg-blue-50 text-blue-700"
                : "text-slate-500 hover:bg-slate-50"
            }`}
          >
            <MapPinned size={18} />
            Разбор адресов
          </button>

          <button
            onClick={() => onNavigate("dashboard")}
            className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition ${
              currentPage === "dashboard"
                ? "bg-blue-50 text-blue-700"
                : "text-slate-500 hover:bg-slate-50"
            }`}
          >
            <Database size={18} />
            Справочник и аналитика
          </button>
        </nav>

        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">
          JA
        </div>
      </div>
    </header>
  );
}
