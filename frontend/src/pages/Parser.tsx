
import { useState } from "react";
import {
  MapPin,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
} from "lucide-react";

import StatCard from "../components/address/StatCard";
import AddressTable from "../components/address/AddressTable";
import type { Address, AddressInput } from "../types/address";



export default function Parser() {
  const [addresses, setAddresses] = useState<Address[]>([]);

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

  function handleUpdate(updated: Address) {
    setAddresses((previous) =>
      previous.map((address) =>
        address.id === updated.id ? updated : address
      )
    );
  }

  function handleFileUpload(imported: AddressInput[]) {
    const rows: Address[] = imported.map((item) => ({
      ...item,
      province: null,
      city: null,
      district: null,
      living_area: null,
      street_type: null,
      street_name: null,
      house: null,
      apartment: null,
      entrance: null,
      floor: null,
      landmark: null,
      confidence: 0,
    }));
    setAddresses((previous) => [...previous, ...rows]);
  }

  return (
    <div>
      <div className="mb-7">
  <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
    <MapPin size={14} />
    Управление доставкой
  </div>

  <h1 className="text-3xl font-bold text-slate-900">
    Адреса доставки
  </h1>

  <p className="mt-2 text-slate-500">
    Добавляйте адреса получателей, проверяйте
    данные и уточняйте информацию для доставки.
  </p>
</div>

      <div className="mb-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Результатов разбора"
          value={addresses.length}
          icon={MapPin}
          color="bg-emerald-100 text-blue-600"
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
        onImport={handleFileUpload}
      />
    </div>
  );
}
