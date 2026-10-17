
import { useState } from "react";
import { Download, Pencil, Search, AlertTriangle } from "lucide-react";
import type { Address } from "../../types/address";
import AddressEditor from "./AddressEditor";
import FileUpload from "../upload/FileUpload";

interface Props {
  addresses: Address[];
  onUpdate: (address: Address) => Promise<void> | void;
  onImport: (file: File) => Promise<void> | void;
  busy?: boolean;
}

export default function AddressTable({
  addresses,
  onUpdate,
  onImport,
  busy = false,
}: Props) {
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Address | null>(null);
  const [page, setPage] = useState(1);

  const filtered = addresses.filter((address) =>
    [
      address.raw_address,
      address.city,
      address.district,
      address.street_name,
      address.house,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const pageSize = 5;
  const totalPages = Math.max(
    1,
    Math.ceil(filtered.length / pageSize)
  );
  const currentPage = Math.min(page, totalPages);
  const visible = filtered.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  function exportJSON() {
    const blob = new Blob(
      [JSON.stringify(addresses, null, 2)],
      { type: "application/json;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "jana_address_results.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function saveAddress(updated: Address) {
    await onUpdate(updated);
    setEditing(null);
  }

  function display(value: string | null) {
    return value ?? "—";
  }

  return (
    <>
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 p-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Результаты обработки
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Всего записей: {addresses.length}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <FileUpload onUpload={onImport} disabled={busy} />
            <button
              onClick={exportJSON}
              disabled={addresses.length === 0}
              className="flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Download size={18} />
              Экспорт JSON
            </button>
          </div>
        </div>

        <div className="p-5">
          <div className="relative max-w-md">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="Поиск по адресам..."
              className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1400px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                {[
                  "ID",
                  "Исходный адрес",
                  "Область",
                  "Город",
                  "Район",
                  "Жилой массив",
                  "Тип улицы",
                  "Улица",
                  "Дом",
                  "Квартира",
                  "Подъезд",
                  "Этаж",
                  "Ориентир",
                  "Confidence",
                  "Действие",
                ].map((title) => (
                  <th
                    key={title}
                    className="whitespace-nowrap px-4 py-4 font-semibold"
                  >
                    {title}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {visible.map((address) => {
                const needsReview = address.needs_review;

                return (
                  <tr
                    key={address.record_id ?? address.id}
                    className={`border-t border-slate-100 ${
                      needsReview
                        ? "bg-amber-50/50"
                        : "hover:bg-slate-50"
                    }`}
                  >
                    <td className="px-4 py-4 text-xs text-slate-500">
                      {address.id}
                    </td>
                    <td className="max-w-xs px-4 py-4 font-medium">
                      <div className="min-w-48">
                        {address.raw_address}
                      </div>
                    </td>
                    <td className="px-4 py-4">{display(address.province)}</td>
                    <td className="px-4 py-4">{display(address.city)}</td>
                    <td className="px-4 py-4">{display(address.district)}</td>
                    <td className="px-4 py-4">{display(address.living_area)}</td>
                    <td className="px-4 py-4">{display(address.street_type)}</td>
                    <td className="px-4 py-4">{display(address.street_name)}</td>
                    <td className="px-4 py-4">{display(address.house)}</td>
                    <td className="px-4 py-4">{display(address.apartment)}</td>
                    <td className="px-4 py-4">{display(address.entrance)}</td>
                    <td className="px-4 py-4">{display(address.floor)}</td>
                    <td className="px-4 py-4">{display(address.landmark)}</td>
                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
                          needsReview
                            ? "bg-amber-100 text-amber-700"
                            : "bg-emerald-100 text-emerald-700"
                        }`}
                      >
                        {needsReview && <AlertTriangle size={13} />}
                        {Math.round(address.confidence * 100)}%
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <button
                        onClick={() => setEditing(address)}
                        title="Исправить адрес"
                        aria-label={`Исправить адрес ${address.id}`}
                        className="rounded-lg p-2 text-blue-600 hover:bg-emerald-50"
                      >
                        <Pencil size={18} />
                      </button>
                    </td>
                  </tr>
                );
              })}

              {visible.length === 0 && (
                <tr>
                  <td
                    colSpan={15}
                    className="px-5 py-12 text-center text-slate-400"
                  >
                    Нет адресов для отображения
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 p-5 text-sm">
          <span className="text-slate-500">
            Страница {currentPage} из {totalPages}
          </span>

          <div className="flex gap-2">
            <button
              disabled={currentPage === 1}
              onClick={() => setPage(currentPage - 1)}
              className="rounded-lg border border-slate-200 px-4 py-2 disabled:opacity-40"
            >
              Назад
            </button>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setPage(currentPage + 1)}
              className="rounded-lg border border-slate-200 px-4 py-2 disabled:opacity-40"
            >
              Далее
            </button>
          </div>
        </div>
      </section>

      {editing && (
        <AddressEditor
          key={editing.id}
          address={editing}
          onSave={saveAddress}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
