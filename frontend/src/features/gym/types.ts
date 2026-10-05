export type Page<T> = {
  count: number;
  next: number | null;
  previous: number | null;
  results: T[];
};
export type Plan = {
  id: string;
  version: number;
  name: string;
  amount: string;
  currency: string;
  unit: "DAYS" | "MONTHS";
  quantity: number;
  is_active: boolean;
  is_promotion: boolean;
  available_from: string | null;
  available_until: string | null;
};
export type Preview = {
  plan_id: string;
  version: number;
  name: string;
  start_date: string;
  end_date: string;
  last_day: string;
  amount: string;
  currency: string;
};
export type Membership = {
  id: string;
  name: string;
  version: number;
  amount: string;
  currency: string;
  start_date: string;
  end_date: string;
  last_day: string | null;
  cancelled_on: string | null;
  status: string;
  remaining_days: number;
  freezes: { start_date: string; end_date: string }[];
  changes: {
    kind: string;
    reason: string;
    before: Record<string, string | null>;
    after: Record<string, string | null>;
    created_at: string;
  }[];
};
export type Charge = {
  id: string;
  source: string;
  label: string;
  amount: string;
  balance: string;
  currency: string;
  created_at: string;
};
export type Payment = {
  id: string;
  amount: string;
  currency: string;
  method: string;
  created_at: string;
  allocations: { charge_id: string; amount: string; refundable: string }[];
  refunds: { id: string; amount: string; reason: string; created_at: string }[];
};
