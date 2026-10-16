
export interface Address {
  id: string;
  raw_address: string;

  province: string | null;
  city: string | null;
  district: string | null;
  living_area: string | null;

  street_type: string | null;
  street_name: string | null;

  house: string | null;
  apartment: string | null;
  entrance: string | null;
  floor: string | null;

  landmark: string | null;
  confidence: number;
}

export interface AddressInput {
  id: string;
  raw_address: string;
}
