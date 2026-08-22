export interface Contact {
  id: string;
  name: string | null;
  company_id: string | null;
  title: string | null;
  contact_mode: string | null;
  warmth: string | null;
  last_connected: string | null;
  next_follow_up: string | null;
  status: string | null;
  hiring_companies: string | null;
  notes: string | null;
}

export interface Company {
  id: string;
  name: string | null;
  stage: string | null;
  interest: string | null;
  industry: string | null;
  role: string | null;
  url: string | null;
  careers_page: string | null;
  notes: string | null;
  contact_names: string[];
}

export const CONTACT_MODES = ["LinkedIn", "Email", "Referral", "Cold", "Event/Conference"] as const;
export const WARMTH_LEVELS = ["Cold", "Warm", "Hot", "Referral Ready"] as const;
export const STATUSES = ["Reached Out", "No Response", "Replied", "Call Scheduled", "Referred", "Interviewing", "Dead End"] as const;
export const COMPANY_STAGES = ["Seed", "Series A", "Series B+", "Public"] as const;
export const INTEREST_LEVELS = ["Low", "Medium", "High"] as const;
export const INDUSTRIES = ["AI", "Bio/Health", "Energy", "Manufacturing", "Consumer", "Enterprise"] as const;
