
import { useState } from "react";
import { Menu, Truck } from "lucide-react";

import Header from "../components/layout/Header";
import type { Page } from "../components/layout/Header";
import Parser from "../pages/Parser";
import Dashboard from "../pages/Dashboard";
import Home from "../pages/Home";
import type { Address } from "../types/address";

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [addresses, setAddresses] = useState<Address[]>([]);

  const titles: Record<Page, string> = {
    home: "Главная · Адреса доставки",
    dashboard: "Справочник и аналитика",
  };

  return (
    <div className="min-h-screen bg-[#F6F8F7]">
      <Header
        currentPage={page}
        onNavigate={setPage}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="min-h-screen lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white px-5 lg:px-9">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileOpen(true)}
              aria-label="Открыть меню"
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            >
              <Menu size={23} />
            </button>

            <div>
              <p className="text-xs font-medium text-slate-400">
                JANA POST / Рабочая панель
              </p>
              <h2 className="text-xl font-bold text-slate-900">
                {titles[page]}
              </h2>
            </div>
          </div>

          <div className="hidden items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 sm:flex">
            <Truck size={17} />
            Служба доставки
          </div>
        </header>

        <main className="mx-auto max-w-[1500px] p-5 lg:p-9">
          {page === "home" && <><Home /><Parser addresses={addresses} setAddresses={setAddresses} /></>}

          {page === "dashboard" && <Dashboard addresses={addresses} />}
        </main>
      </div>
    </div>
  );
}
