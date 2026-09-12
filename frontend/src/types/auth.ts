export type UserRole = 'ADMIN' | 'DATA_SCIENTIST' | 'USER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  expires_in: number;
}
