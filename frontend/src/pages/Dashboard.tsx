
import { Database } from "lucide-react";

export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-slate-900">
        Справочник и аналитика
      </h1>

      <p className="mt-2 text-slate-500">
        Географический справочник Казахстана и статистика обработки
      </p>

      <div className="mt-7 rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <Database size={40} className="mx-auto text-blue-600" />
        <h2 className="mt-4 text-lg font-bold">
          Географический справочник
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Здесь будет таблица городов, районов, улиц и аналитика.
        </p>
      </div>
    </div>
  );
}
