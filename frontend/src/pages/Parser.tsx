
import { MapPin } from "lucide-react";

import AddressForm from "../components/address/AddressForm";
import AddressTable from "../components/address/AddressTable";
import type { Address, AddressInput } from "../types/address";

interface ParserProps {
  addresses: Address[];
  setAddresses: (updater: (previous: Address[]) => Address[]) => void;
}

export default function Parser({ addresses, setAddresses }: ParserProps) {

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

  function handleManualAdd(rawAddresses: string[]) {
    handleFileUpload(rawAddresses.map((raw_address, index) => ({
      id: `rec_${Date.now()}_${index + 1}_${Math.random().toString(36).slice(2, 6)}`,
      raw_address,
    })));
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

      <div className="mb-7 max-w-2xl">
        <AddressForm onParse={handleManualAdd} />
      </div>

      <AddressTable
        addresses={addresses}
        onUpdate={handleUpdate}
        onImport={handleFileUpload}
      />
    </div>
  );
}
