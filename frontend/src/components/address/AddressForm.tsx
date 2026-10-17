
import { useState } from "react";
import { MapPin, Search } from "lucide-react";

interface AddressFormProps {
  onParse: (addresses: string[]) => void;
}

export default function AddressForm({ onParse }: AddressFormProps) {
  const [input, setInput] = useState("");

  function handleSubmit() {
    const addresses = input
      .split("\n")
      .map((address) => address.trim())
      .filter(Boolean);

    if (addresses.length === 0) return;

    onParse(addresses);
    setInput("");
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <MapPin className="text-blue-600" size={22} />
        <h2 className="text-lg font-bold text-slate-900">
          Ввод адреса
        </h2>
      </div>

      <p className="mb-3 text-sm text-slate-500">
        Введите один или несколько адресов, каждый с новой строки
      </p>

      <textarea
        value={input}
        onChange={(event) => setInput(event.target.value)}
        placeholder={
          "г. Алматы, ул. Абая, 25, кв. 12\nАстана, проспект Республики, 45"
        }
        className="h-40 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />

      <button
        onClick={handleSubmit}
        disabled={!input.trim()}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Search size={18} />
        Разобрать адреса
      </button>
    </section>
  );
}
