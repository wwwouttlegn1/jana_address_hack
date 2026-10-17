
import {
  ArrowRight,
  ClipboardCheck,
  FileUp,
  MapPin,
  BookOpen,
  ShieldCheck,
  Truck,
} from "lucide-react";

import type { Page } from "../components/layout/Header";

interface HomeProps {
  onNavigate: (page: Page) => void;
}

export default function Home({ onNavigate }: HomeProps) {
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-3xl bg-emerald-800 p-7 text-white md:p-10">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-xs font-semibold">
            <Truck size={16} />
            Логистическая платформа
          </div>

          <h1 className="text-3xl font-extrabold leading-tight md:text-4xl">
            Доставка начинается
            <br />
            с точного адреса
          </h1>

          <p className="mt-5 max-w-xl text-sm leading-7 text-emerald-100 md:text-base">
            Управляйте адресами доставки, проверяйте
            данные получателей и уточняйте информацию
            до передачи заказа курьеру.
          </p>

          <button
            onClick={() => onNavigate("parser")}
            className="mt-7 inline-flex items-center gap-3 rounded-xl bg-white px-6 py-3 font-bold text-emerald-800 transition hover:bg-emerald-50"
          >
            Перейти к адресам
            <ArrowRight size={19} />
          </button>
        </div>

        <Truck
          size={220}
          strokeWidth={0.7}
          className="absolute -bottom-12 -right-10 text-white/10"
        />
      </section>

      <div>
        <h2 className="text-xl font-bold text-slate-900">
          Рабочие инструменты
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Всё необходимое для подготовки адресов доставки
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <button
          onClick={() => onNavigate("parser")}
          className="group rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:border-emerald-300 hover:shadow-md"
        >
          <div className="mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
            <MapPin size={26} />
          </div>

          <h3 className="text-lg font-bold text-slate-900">
            Адреса доставки
          </h3>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Добавление адресов, проверка заполненных
            полей и исправление неточностей.
          </p>

          <div className="mt-6 flex items-center gap-2 text-sm font-bold text-emerald-700">
            Открыть раздел
            <ArrowRight
              size={17}
              className="transition group-hover:translate-x-1"
            />
          </div>
        </button>

        <button
          onClick={() => onNavigate("dashboard")}
          className="group rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:border-emerald-300 hover:shadow-md"
        >
          <div className="mb-5 flex h-13 w-13 items-center justify-center rounded-2xl bg-teal-100 text-teal-700">
            <BookOpen size={26} />
          </div>

          <h3 className="text-lg font-bold text-slate-900">
            Справочник и аналитика
          </h3>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Географические данные, районы,
            населённые пункты и аналитика адресов.
          </p>

          <div className="mt-6 flex items-center gap-2 text-sm font-bold text-emerald-700">
            Открыть раздел
            <ArrowRight
              size={17}
              className="transition group-hover:translate-x-1"
            />
          </div>
        </button>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          Как подготовить адреса к доставке
        </h2>

        <div className="mt-6 grid gap-6 md:grid-cols-3">
          {[
            {
              icon: FileUp,
              number: "01",
              title: "Добавьте адреса",
              description:
                "Введите адрес вручную или импортируйте файл.",
            },
            {
              icon: ClipboardCheck,
              number: "02",
              title: "Проверьте данные",
              description:
                "Получите структурированные поля адреса.",
            },
            {
              icon: ShieldCheck,
              number: "03",
              title: "Уточните и сохраните",
              description:
                "Исправьте неточности и выгрузите результат.",
            },
          ].map((step) => {
            const Icon = step.icon;

            return (
              <div key={step.number} className="flex gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                  <Icon size={21} />
                </div>

                <div>
                  <span className="text-xs font-bold text-emerald-600">
                    ШАГ {step.number}
                  </span>
                  <h3 className="mt-1 font-semibold text-slate-900">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
