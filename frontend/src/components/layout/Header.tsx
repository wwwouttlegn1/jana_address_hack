
import {
  LayoutDashboard,
  BookOpen,
  Truck,
  X,
} from "lucide-react";

export type Page = "home" | "dashboard";

interface HeaderProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

const navigation = [
  {
    id: "home" as const,
    label: "Главная",
    icon: LayoutDashboard,
  },
  {
    id: "dashboard" as const,
    label: "Справочник и аналитика",
    icon: BookOpen,
  },
];

export default function Header({
  currentPage,
  onNavigate,
  mobileOpen,
  onCloseMobile,
}: HeaderProps) {
  function navigate(page: Page) {
    onNavigate(page);
    onCloseMobile();
  }

  return (
    <>
      {mobileOpen && (
        <button
          aria-label="Закрыть меню"
          onClick={onCloseMobile}
          className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center justify-between border-b border-slate-100 px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-700">
              <Truck size={23} className="text-white" />
            </div>
            <div>
              <p className="text-sm font-extrabold text-slate-900">JANA ADDRESS</p>
              <p className="text-xs text-slate-400">JANA POST</p>
            </div>
          </div>

          <button
            onClick={onCloseMobile}
            aria-label="Закрыть меню"
            className="text-slate-500 lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-4 pt-7">
          <p className="mb-3 px-3 text-xs font-bold uppercase tracking-wider text-slate-400">
            Рабочая панель
          </p>

          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = currentPage === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => navigate(item.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-semibold transition ${
                    active
                      ? "bg-emerald-50 text-emerald-800"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <Icon size={19} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto border-t border-slate-100 p-5">
          <div className="rounded-xl bg-emerald-50 p-4">
            <p className="text-sm font-semibold text-emerald-900">
              Проверка адресов
            </p>
            <p className="mt-1 text-xs leading-5 text-emerald-700">
              Подготовка адресов для точной доставки
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
