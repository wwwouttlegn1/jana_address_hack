
import { useState } from "react";
import { MapPin, Plus } from "lucide-react";

interface AddressFormProps {
  onParse: (addresses: string[]) => Promise<void> | void;
  disabled?: boolean;
}

export default function AddressForm({ onParse, disabled = false }: AddressFormProps) {
  const [input, setInput] = useState("");

  async function handleSubmit() {
    const addresses = input
      .split("\n")
      .map((address) => address.trim())
      .filter(Boolean);

    if (addresses.length === 0) return;

    try {
      await onParse(addresses);
      setInput("");
    } catch {
      // Parent displays the API error and keeps the entered address for retry.
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <MapPin className="text-blue-600" size={22} />
        <h2 className="text-lg font-bold text-slate-900">
          Добавить адрес вручную
        </h2>
      </div>

      <p className="mb-3 text-sm text-slate-500">
        Введите один или несколько адресов, каждый с новой строки. Они появятся в таблице.
      </p>

      <textarea
        value={input}
        onChange={(event) => setInput(event.target.value)}
        placeholder={
          "г. Алматы, ул. Абая, 25, кв. 12\nАстана, проспект Республики, 45"
        }
        className="h-40 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
      />

      <button
        onClick={handleSubmit}
        disabled={!input.trim() || disabled}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Plus size={18} />
        {disabled ? "Обработка..." : "Разобрать адрес"}
      </button>
    </section>
  );
}
