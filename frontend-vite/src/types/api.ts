// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// User Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  role: string;
  balance?: number;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Project Types
export interface Project {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  metadata?: Record<string, any>;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  metadata?: Record<string, any>;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  is_archived?: boolean;
  metadata?: Record<string, any>;
}

// Folder Types
export interface Folder {
  id: number;
  name: string;
  project_id: number;
  parent_folder_id?: number;
  created_at: string;
  updated_at: string;
  color?: string;
  icon?: string;
  path?: string;
}

export interface FolderCreate {
  name: string;
  project_id: number;
  parent_folder_id?: number;
  color?: string;
  icon?: string;
}

export interface FolderUpdate {
  name?: string;
  parent_folder_id?: number;
  color?: string;
  icon?: string;
}

// Chat Types
export interface Chat {
  id: number;
  title: string;
  project_id: number;
  folder_id?: number;
  created_at: string;
  updated_at: string;
  system_prompt?: string;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  is_archived: boolean;
  metadata?: Record<string, any>;
}

export interface ChatCreate {
  title: string;
  project_id: number;
  folder_id?: number;
  system_prompt?: string;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  metadata?: Record<string, any>;
}

export interface ChatUpdate {
  title?: string;
  folder_id?: number;
  system_prompt?: string;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  is_archived?: boolean;
  metadata?: Record<string, any>;
}

// Message Types
export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: number;
  chat_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
  token_count?: number;
  model_name?: string;
  metadata?: Record<string, any>;
}

export interface MessageCreate {
  chat_id: number;
  role: MessageRole;
  content: string;
  token_count?: number;
  model_name?: string;
  metadata?: Record<string, any>;
}

// Search Types
export interface SearchResults {
  projects?: Project[];
  chats?: Chat[];
  messages?: Message[];
}

// LLM Types
export interface LLMProvider {
  id: string;
  name: string;
  models: LLMModel[];
  enabled: boolean;
}

export interface LLMModel {
  id: string;
  name: string;
  provider: string;
  max_tokens: number;
  cost_per_token: number;
  supports_streaming: boolean;
  supports_functions: boolean;
}

export interface LLMRequest {
  model: string;
  messages: Array<{
    role: MessageRole;
    content: string;
  }>;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  system_prompt?: string;
}

export interface LLMResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: MessageRole;
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  cost?: number;
}

// Pagination Types
export interface PaginationParams {
  skip?: number;
  limit?: number;
  search?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Error Types
export interface ApiError {
  error: string;
  message: string;
  status_code: number;
  details?: Record<string, any>;
}

// API Key Types
export interface ApiKey {
  id: number;
  name: string;
  key_preview: string;
  created_at: string;
  last_used?: string;
  is_active: boolean;
}

export interface ApiKeyCreate {
  name: string;
}

export interface ApiKeyResponse {
  key: ApiKey;
  key_value: string; // Nur beim Erstellen zurückgegeben
} 