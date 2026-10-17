import { AlertTriangle, Check, CircleAlert, Database, Sparkles } from "lucide-react";
import type { Address } from "../types/address";

interface DashboardProps {
  addresses: Address[];
}

const cardBase = "rounded-xl border border-slate-200 bg-white p-5 shadow-sm";

export default function Dashboard({ addresses }: DashboardProps) {
  const total = addresses.length;
  const processed = addresses.filter((address) => !address.needs_review).length;
  const needsReview = total - processed;
  const avgConfidence = total
    ? Math.round((addresses.reduce((sum, address) => sum + address.confidence, 0) / total) * 100)
    : 0;
  const missing = {
    city: addresses.filter((address) => !address.city).length,
    street: addresses.filter((address) => !address.street_name).length,
    house: addresses.filter((address) => !address.house).length,
    extra: addresses.filter((address) => !address.district && !address.apartment).length,
  };
  const fields = [
    { label: "Город", value: addresses.filter((address) => address.city).length, color: "bg-blue-600" },
    { label: "Улица", value: addresses.filter((address) => address.street_name).length, color: "bg-sky-500" },
    { label: "Дом", value: addresses.filter((address) => address.house).length, color: "bg-indigo-900" },
    { label: "Доп. поля", value: addresses.filter((address) => address.district || address.apartment).length, color: "bg-slate-300" },
  ];
  const filledPercent = total
    ? Math.round((fields.reduce((sum, field) => sum + field.value, 0) / (total * fields.length)) * 100)
    : 0;
  const errors = [
    { label: "Не указана улица", value: missing.street },
    { label: "Не указан дом", value: missing.house },
    { label: "Не указан город", value: missing.city },
    { label: "Нет дополнительных полей", value: missing.extra },
  ];
  const maxError = Math.max(1, ...errors.map((error) => error.value));
  const latest = [...addresses].slice(-5).reverse();

  const cards = [
    { title: "Всего адресов", value: total.toLocaleString("ru-RU"), note: "В текущем списке", icon: Database, iconClass: "bg-blue-50 text-blue-600" },
    { title: "Обработано", value: processed.toLocaleString("ru-RU"), note: "Готово к использованию", icon: Check, iconClass: "bg-emerald-50 text-emerald-600" },
    { title: "На проверке", value: needsReview.toLocaleString("ru-RU"), note: "Требует уточнения", icon: AlertTriangle, iconClass: "bg-amber-50 text-amber-600" },
    { title: "Ср. уверенность", value: `${avgConfidence}%`, note: "По данным таблицы", icon: Sparkles, iconClass: "bg-violet-50 text-violet-600" },
    { title: "Ошибки полей", value: (missing.city + missing.street + missing.house).toLocaleString("ru-RU"), note: "Город, улица и дом", icon: CircleAlert, iconClass: "bg-rose-50 text-rose-600" },
    { title: "Источник", value: "Локальные данные", note: "Импорт и ручной ввод", icon: Database, iconClass: "bg-slate-100 text-slate-600" },
  ];

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Статистика обработки</h1>
          <p className="mt-1 text-sm text-slate-500">Показатели рассчитаны по адресам в таблице</p>
        </div>
        <span className="text-xs text-slate-400">Обновляется при изменении списка</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {cards.map(({ title, value, note, icon: Icon, iconClass }) => (
          <section className={cardBase} key={title}>
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm text-slate-500">{title}</p>
              <span className={`rounded-lg p-2 ${iconClass}`}><Icon size={18} /></span>
            </div>
            <p className="mt-2 text-xl font-bold text-slate-900">{value}</p>
            <p className="mt-1 text-xs text-slate-400">{note}</p>
          </section>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        <section className={`${cardBase} p-6`}>
          <h2 className="font-semibold text-slate-900">Заполненность полей</h2>
          <p className="mt-1 text-xs text-slate-500">Доля заполненных компонентов адреса</p>
          {total ? <div className="mt-6 grid items-center gap-6 sm:grid-cols-[180px_1fr]">
            <div className="mx-auto flex h-40 w-40 items-center justify-center rounded-full" style={{ background: `conic-gradient(#2563eb ${filledPercent * 3.6}deg, #e2e8f0 0deg)` }}>
              <div className="flex h-28 w-28 flex-col items-center justify-center rounded-full bg-white">
                <span className="text-2xl font-bold text-slate-900">{filledPercent}%</span>
                <span className="text-xs text-slate-400">в среднем</span>
              </div>
            </div>
            <div className="space-y-4">
              {fields.map((field) => {
                const percent = Math.round((field.value / total) * 100);
                return <div key={field.label} className="grid grid-cols-[70px_1fr_38px] items-center gap-3 text-sm">
                  <span className="text-slate-600">{field.label}</span>
                  <div className="h-2 rounded-full bg-slate-100"><div className={`h-2 rounded-full ${field.color}`} style={{ width: `${percent}%` }} /></div>
                  <span className="text-right font-semibold text-slate-700">{percent}%</span>
                </div>;
              })}
            </div>
          </div> : <p className="mt-8 rounded-lg bg-slate-50 p-6 text-center text-sm text-slate-500">Добавьте адрес вручную или импортируйте файл — здесь появится статистика.</p>}
        </section>

        <section className={`${cardBase} p-6`}>
          <h2 className="font-semibold text-slate-900">Частые ошибки</h2>
          <p className="mt-1 text-xs text-slate-500">Незаполненные поля в адресах</p>
          <div className="mt-7 space-y-5">
            {errors.map((error) => <div key={error.label} className="grid grid-cols-[125px_1fr_32px] items-center gap-3 text-xs sm:grid-cols-[145px_1fr_36px] sm:text-sm">
              <span className="text-slate-600">{error.label}</span>
              <div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-orange-400" style={{ width: `${(error.value / maxError) * 100}%` }} /></div>
              <span className="text-right font-semibold text-slate-700">{error.value}</span>
            </div>)}
          </div>
        </section>
      </div>

      <section className={`${cardBase} mt-5 overflow-hidden p-0`}>
        <div className="border-b border-slate-100 p-5">
          <h2 className="font-semibold text-slate-900">Последние адреса</h2>
          <p className="mt-1 text-xs text-slate-500">Недавно добавленные записи из текущего списка</p>
        </div>
        {latest.length ? <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-5 py-3">ID</th><th className="px-5 py-3">Исходный адрес</th><th className="px-5 py-3">Уверенность</th><th className="px-5 py-3">Статус</th></tr></thead>
            <tbody>{latest.map((address) => <tr key={address.record_id ?? address.id} className="border-t border-slate-100"><td className="px-5 py-3 text-slate-500">{address.id}</td><td className="px-5 py-3 font-medium text-slate-800">{address.raw_address}</td><td className="px-5 py-3">{Math.round(address.confidence * 100)}%</td><td className="px-5 py-3"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${!address.needs_review ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{!address.needs_review ? "Обработан" : "Нужна проверка"}</span></td></tr>)}</tbody>
          </table>
        </div> : <p className="p-8 text-center text-sm text-slate-500">Пока нет добавленных адресов.</p>}
      </section>
    </div>
  );
}
