export type ClientRecord = {
  id: string;
  full_name: string;
  phone: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
export type ClientPage = {
  count: number;
  next: string | null;
  previous: string | null;
  results: ClientRecord[];
};
