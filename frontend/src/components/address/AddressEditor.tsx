
import { useState } from "react";
import type { FormEvent } from "react";
import { X, Save, Pencil } from "lucide-react";
import type { Address } from "../../types/address";

interface Props {
  address: Address;
  onSave: (address: Address) => Promise<void> | void;
  onClose: () => void;
}

const fields = [
  ["province", "Область"],
  ["city", "Город"],
  ["district", "Район"],
  ["living_area", "Жилой массив / ЖК"],
  ["street_type", "Тип улицы"],
  ["street_name", "Название улицы"],
  ["house", "Дом"],
  ["apartment", "Квартира"],
  ["entrance", "Подъезд"],
  ["floor", "Этаж"],
  ["landmark", "Ориентир"],
] as const;

export default function AddressEditor({
  address,
  onSave,
  onClose,
}: Props) {
  const [draft, setDraft] = useState<Address>({ ...address });
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSave(draft);
    } catch {
      // Ошибка отображается в родительском компоненте, редактор остаётся открытым.
    } finally {
      setSaving(false);
    }
  }

  function updateField(
    field: (typeof fields)[number][0],
    value: string
  ) {
    setDraft((previous) => ({
      ...previous,
      [field]: value.trim() === "" ? null : value,
    }));
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="editor-title"
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Pencil size={20} className="text-blue-600" />
              <h2
                id="editor-title"
                className="text-xl font-bold text-slate-900"
              >
                Ручное исправление адреса
              </h2>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              Проверьте поля и внесите исправления
            </p>
          </div>

          <button
            onClick={onClose}
            aria-label="Закрыть"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
          >
            <X size={20} />
          </button>
        </div>

        <div className="mb-6 rounded-xl bg-slate-50 p-4">
          <p className="mb-1 text-xs font-semibold uppercase text-slate-400">
            Исходный адрес
          </p>
          <p className="text-sm font-medium text-slate-800">
            {address.raw_address}
          </p>
        </div>

        <form onSubmit={submit}>
          <div className="grid gap-4 sm:grid-cols-2">
            {fields.map(([key, label]) => (
              <label key={key} className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">
                  {label}
                </span>
                <input
                  value={draft[key] ?? ""}
                  onChange={(event) =>
                    updateField(key, event.target.value)
                  }
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                  placeholder="Не определено"
                />
              </label>
            ))}
          </div>

          <div className="mt-7 flex justify-end gap-3 border-t border-slate-100 pt-5">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Save size={17} />
              {saving ? "Сохраняем…" : "Сохранить изменения"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
