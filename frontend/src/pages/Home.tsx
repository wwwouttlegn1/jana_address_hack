import { MapPin, Truck } from "lucide-react";

export default function Home() {
  return (
    <section className="mb-8 flex items-center gap-5 rounded-3xl bg-emerald-800 p-7 text-white md:p-9">
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white/10">
        <MapPin size={28} />
      </div>
      <div>
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-emerald-100">
          <Truck size={15} /> JANA POST
        </div>
        <h1 className="text-2xl font-extrabold md:text-3xl">Адреса доставки</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-emerald-100">
          Загружайте адреса из файла, проверяйте записи в таблице и экспортируйте результат.
        </p>
      </div>
    </section>
  );
}
