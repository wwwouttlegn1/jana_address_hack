import { useState } from "react";
import { AlertCircle, MapPin } from "lucide-react";

import AddressForm from "../components/address/AddressForm";
import AddressTable from "../components/address/AddressTable";
import { parseBatch, parseFile } from "../services/api";
import type { Address, AddressInput } from "../types/address";

interface ParserProps {
  addresses: Address[];
  setAddresses: (updater: (previous: Address[]) => Address[]) => void;
}

export default function Parser({ addresses, setAddresses }: ParserProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleUpdate(updated: Address) {
    setAddresses((previous) =>
      previous.map((address) =>
        address.id === updated.id ? updated : address,
      ),
    );
  }

  async function handleFileUpload(file: File) {
    setBusy(true);
    setError(null);
    try {
      const parsed = await parseFile(file);
      setAddresses((previous) => [...previous, ...parsed]);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Не удалось обработать файл",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleManualAdd(rawAddresses: string[]) {
    const items: AddressInput[] = rawAddresses.map((raw_address, index) => ({
      id: `rec_${Date.now()}_${index + 1}_${Math.random().toString(36).slice(2, 6)}`,
      raw_address,
    }));

    setBusy(true);
    setError(null);
    try {
      const parsed = await parseBatch(items);
      setAddresses((previous) => [...previous, ...parsed]);
    } catch (reason) {
      const message =
        reason instanceof Error ? reason.message : "Не удалось обработать адрес";
      setError(message);
      throw reason;
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="mb-7">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
          <MapPin size={14} />
          Управление доставкой
        </div>

        <h1 className="text-3xl font-bold text-slate-900">Адреса доставки</h1>
        <p className="mt-2 text-slate-500">
          Добавляйте адреса получателей — backend разберёт строку и уточнит
          данные по справочнику PostgreSQL.
        </p>
      </div>

      <div className="mb-7 max-w-2xl">
        <AddressForm onParse={handleManualAdd} disabled={busy} />
      </div>

      {error && (
        <div className="mb-5 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <AlertCircle className="mt-0.5 shrink-0" size={18} />
          <div>
            <p className="font-semibold">Backend не обработал запрос</p>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      <AddressTable
        addresses={addresses}
        onUpdate={handleUpdate}
        onImport={handleFileUpload}
        busy={busy}
      />
    </div>
  );
}
