
import type { Address, AddressInput } from "../types/address";

const API_URL = (import.meta.env.VITE_API_URL ?? "/api/v1").replace(/\/$/, "");

async function readApiError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || `Ошибка API: ${response.status}`;
  } catch {
    return `Ошибка API: ${response.status}`;
  }
}

export async function parseAddress(address: AddressInput): Promise<Address> {
  const response = await fetch(`${API_URL}/parse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(address),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return response.json() as Promise<Address>;
}

export async function parseBatch(addresses: AddressInput[]): Promise<Address[]> {
  const response = await fetch(`${API_URL}/parse/batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(addresses),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return response.json() as Promise<Address[]>;
}

export async function parseFile(file: File): Promise<Address[]> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_URL}/parse/file`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  return response.json() as Promise<Address[]>;
}

export async function loadRecords(limit = 500): Promise<Address[]> {
  const response = await fetch(`${API_URL}/records?limit=${limit}`);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json() as Promise<Address[]>;
}

export async function updateRecord(address: Address): Promise<Address> {
  if (!address.record_id) {
    throw new Error("У записи отсутствует ID PostgreSQL");
  }
  const {
    province,
    city,
    district,
    living_area,
    street_type,
    street_name,
    house,
    apartment,
    entrance,
    floor,
    landmark,
  } = address;
  const response = await fetch(`${API_URL}/records/${address.record_id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      province,
      city,
      district,
      living_area,
      street_type,
      street_name,
      house,
      apartment,
      entrance,
      floor,
      landmark,
    }),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json() as Promise<Address>;
}
