
import { useState } from "react";
import {
  MapPin,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
} from "lucide-react";

import AddressForm from "../components/address/AddressForm";
import FileUpload from "../components/upload/FileUpload";
import StatCard from "../components/address/StatCard";
import AddressTable from "../components/address/AddressTable";
import type { Address } from "../types/address";



export default function Parser() {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [pending, setPending] = useState<string[]>([]);

  const successful = addresses.filter(
    (address) => address.confidence >= 0.85
  ).length;

  const needsReview = addresses.filter(
    (address) => address.confidence < 0.85
  ).length;

  const averageConfidence = addresses.length
    ? Math.round(
        (addresses.reduce(
          (sum, address) => sum + address.confidence,
          0
        ) /
          addresses.length) *
          100
      )
    : 0;

  function handleInput(newAddresses: string[]) {
    setPending((previous) => [...previous, ...newAddresses]);
  }

  function handleUpdate(updated: Address) {
    setAddresses((previous) =>
      previous.map((address) =>
        address.id === updated.id ? updated : address
      )
    );
  }

  return (
    <div>
      <div className="mb-7">
        <h1 className="text-3xl font-bold text-slate-900">
          Разбор адресов
        </h1>
        <p className="mt-2 text-slate-500">
          Преобразуйте неструктурированные адреса в структурированные данные
        </p>
      </div>

      <div className="mb-7 grid gap-6 lg:grid-cols-2">
        <AddressForm onParse={handleInput} />
        <FileUpload onUpload={handleInput} />
      </div>

      {pending.length > 0 && (
        <div className="mb-7 rounded-xl border border-blue-200 bg-blue-50 p-5">
          <h2 className="font-semibold text-blue-900">
            Ожидают обработки: {pending.length}
          </h2>
          <p className="mt-2 text-sm text-blue-700">
            Адреса приняты интерфейсом. После подключения FastAPI
            они будут отправляться на разбор.
          </p>
          <div className="mt-3 max-h-32 space-y-1 overflow-y-auto text-sm text-slate-700">
            {pending.map((address, index) => (
              <p key={index}>{address}</p>
            ))}
          </div>
          <button
            onClick={() => setPending([])}
            className="mt-4 rounded-lg bg-white px-4 py-2 text-sm font-medium text-blue-700"
          >
            Очистить очередь
          </button>
        </div>
      )}

      <div className="mb-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Результатов разбора"
          value={addresses.length}
          icon={MapPin}
          color="bg-blue-100 text-blue-600"
        />
        <StatCard
          title="Высокая уверенность"
          value={successful}
          icon={CheckCircle2}
          color="bg-emerald-100 text-emerald-600"
        />
        <StatCard
          title="Требуют проверки"
          value={needsReview}
          icon={AlertTriangle}
          color="bg-amber-100 text-amber-600"
        />
        <StatCard
          title="Средний confidence"
          value={`${averageConfidence}%`}
          icon={BarChart3}
          color="bg-violet-100 text-violet-600"
        />
      </div>

      <div className="mb-3 text-xs text-slate-400">
        Ниже представлены демонстрационные результаты для проверки интерфейса.
      </div>

      <AddressTable
        addresses={addresses}
        onUpdate={handleUpdate}
      />
    </div>
  );
}
