
import { useRef } from "react";
import type { ChangeEvent } from "react";
import { Upload } from "lucide-react";
import type { AddressInput } from "../../types/address";

interface FileUploadProps {
  onUpload: (addresses: AddressInput[]) => void;
}

export default function FileUpload({ onUpload }: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      let addresses: AddressInput[] = [];

      if (file.name.toLowerCase().endsWith(".json")) {
        const data: unknown = JSON.parse(content);

        const items = Array.isArray(data)
          ? data
          : typeof data === "object" &&
              data !== null &&
              "addresses" in data &&
              Array.isArray(data.addresses)
            ? data.addresses
            : typeof data === "object" && data !== null && "raw_address" in data
              ? [data]
              : [];

        addresses = items
          .map((item: unknown) => {
            if (typeof item === "string" && item.trim()) {
              return {
                id: `rec_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
                raw_address: item.trim(),
              };
            }

            if (
              typeof item === "object" &&
              item !== null &&
              "raw_address" in item &&
              typeof item.raw_address === "string"
            ) {
              return {
                id: "id" in item && typeof item.id === "string" && item.id.trim()
                  ? item.id
                  : `rec_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
                raw_address: item.raw_address,
              };
            }

            return "";
          })
          .filter((item): item is AddressInput =>
            typeof item === "object" && item !== null && Boolean(item.raw_address.trim())
          );
      } else {
        // Упрощённый CSV: один адрес в строке, без сложных кавычек.
        addresses = content
          .split(/\r?\n/)
          .map((line) => line.trim())
          .filter(Boolean)
          .filter((line, index) =>
            !(index === 0 && /^raw_address$/i.test(line))
          )
          .map((raw_address, index) => ({ id: `rec_${Date.now()}_${index + 1}`, raw_address }));
      }

      if (!addresses.length) {
        alert("В файле не найдены адреса");
        return;
      }

      onUpload(addresses);
    } catch {
      alert("Ошибка чтения файла. Проверьте формат JSON или CSV.");
    } finally {
      event.target.value = "";
    }
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,.csv"
        onChange={handleFile}
        className="hidden"
      />

      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        <Upload size={18} />
        Импорт JSON
      </button>
    </>
  );
}
