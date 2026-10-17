
import { useRef } from "react";
import type { ChangeEvent } from "react";
import { Upload, FileJson } from "lucide-react";

interface FileUploadProps {
  onUpload: (addresses: string[]) => void;
}

export default function FileUpload({ onUpload }: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const content = await file.text();
      let addresses: string[] = [];

      if (file.name.toLowerCase().endsWith(".json")) {
        const data: unknown = JSON.parse(content);

        const items = Array.isArray(data)
          ? data
          : typeof data === "object" &&
              data !== null &&
              "addresses" in data &&
              Array.isArray(data.addresses)
            ? data.addresses
            : [];

        addresses = items
          .map((item: unknown) => {
            if (typeof item === "string") return item;

            if (
              typeof item === "object" &&
              item !== null &&
              "raw_address" in item &&
              typeof item.raw_address === "string"
            ) {
              return item.raw_address;
            }

            return "";
          })
          .filter(Boolean);
      } else {
        // Упрощённый CSV: один адрес в строке, без сложных кавычек.
        addresses = content
          .split(/\r?\n/)
          .map((line) => line.trim())
          .filter(Boolean)
          .filter((line, index) =>
            !(index === 0 && /^raw_address$/i.test(line))
          );
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
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <Upload className="text-blue-600" size={22} />
        <h2 className="text-lg font-bold text-slate-900">
          Загрузка файла
        </h2>
      </div>

      <p className="mb-3 text-sm text-slate-500">
        Загрузите файл с адресами в формате JSON или CSV
      </p>

      <input
        ref={fileInputRef}
        type="file"
        accept=".json,.csv"
        onChange={handleFile}
        className="hidden"
      />

      <button
        onClick={() => fileInputRef.current?.click()}
        className="flex h-40 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-blue-200 bg-blue-50/50 transition hover:bg-blue-50"
      >
        <FileJson size={32} className="mb-3 text-blue-600" />
        <span className="font-semibold text-blue-700">
          Нажмите для выбора файла
        </span>
        <span className="mt-1 text-xs text-slate-400">
          JSON или CSV
        </span>
      </button>

      <p className="mt-4 text-center text-xs text-slate-400">
        Файл обрабатывается локально
      </p>
    </section>
  );
}
