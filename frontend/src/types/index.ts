// Personnel types
export interface Personnel {
  id: string;
  name: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  rank: string;
  type: 'military' | 'civilian';
  position?: string;
  phone?: string;
  email?: string;
  status: 'front_desk' | 'admin_room' | 'terminal' | 'float' | 'leave' | 'appointment';
  previous_status?: string;
  appointment_type?: string;
  last_updated?: string;
  created_at?: string;
  avatar?: string;
}

// Appointment types
export interface Appointment {
  id: string;
  personnel_name: string;
  personnel_rank?: string;
  personnel_type?: string;
  status?: string;
  absence_type: string;
  appointment_date: string;
  end_date?: string;  // For multi-day appointments
  start_time?: string;
  end_time?: string;
  duration_hours?: number;
  all_day: boolean;
  original_text?: string;
  created_timestamp?: string;
  category_color?: string;
}

// Manning status
export interface ManningStatus {
  total: number;
  available: number;
  unavailable: number;
  message?: string;
}

// Contact information
export interface Contact {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  last_contact?: string;
  notes?: string;
}

// Personnel status response
export interface PersonnelStatusResponse {
  success: boolean;
  stats: {
    total_personnel: number;
    military_count: number;
    civilian_count: number;
    working_count: number;
    out_of_office_count: number;
  };
  assignments: {
    terminal: { count: number; personnel: Personnel[] };
    admin_room: { count: number; personnel: Personnel[] };
    floor: { count: number; personnel: Personnel[] };
    float: { count: number; personnel: Personnel[] };
  };
  unavailable_personnel: Personnel[];
  real_time_updates: any;
  timestamp: string;
}

// AI Agent response
export interface AIAgentResponse {
  success: boolean;
  ai_response: string;
  response: string;
  message_type: string;
}