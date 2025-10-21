// Base types matching backend models

export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Competitor {
  id: number
  name: string
  domain: string | null
  industry: string | null
  user_id: number
  created_at: string
  updated_at: string
}

export interface DataSource {
  id: number
  competitor_id: number
  source_type: string
  url: string
  is_active: boolean
  last_scraped: string | null
  created_at: string
  updated_at: string
}

export interface ProcessedInsight {
  id: number
  raw_content_id: number
  summary: string
  key_points: string[] | null
  sentiment: 'positive' | 'negative' | 'neutral'
  insights: string | null
  quality_score: number | null
  created_at: string
  updated_at: string
}

export interface Alert {
  id: number
  user_id: number
  competitor_id: number | null
  alert_type: 'sentiment_change' | 'new_content' | 'keyword_match'
  conditions: Record<string, unknown> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Notification {
  id: number
  user_id: number
  alert_id: number | null
  message: string
  is_read: boolean
  created_at: string
}

export interface SavedSearch {
  id: number
  user_id: number
  name: string
  search_type: 'semantic' | 'traditional'
  query: string
  filters: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface SearchHistory {
  id: number
  user_id: number
  search_type: 'semantic' | 'traditional'
  query: string
  filters: Record<string, unknown> | null
  results_count: number | null
  executed_at: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  message: string
  detail?: string
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}
