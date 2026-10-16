
import type { Address, AddressInput } from "../types/address";

const API_URL = "/api";

// Разбор одного адреса
export async function parseAddress(
  address: AddressInput
): Promise<Address> {
  const response = await fetch(`${API_URL}/addresses/parse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(address),
  });

  if (!response.ok) {
    throw new Error("Ошибка обработки адреса");
  }

  return response.json();
}

// Разбор нескольких адресов
export async function parseBatch(
  addresses: AddressInput[]
): Promise<Address[]> {
  const response = await fetch(`${API_URL}/batches/parse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(addresses),
  });

  if (!response.ok) {
    throw new Error("Ошибка пакетной обработки");
  }

  return response.json();
}
