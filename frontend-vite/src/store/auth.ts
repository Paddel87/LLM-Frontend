import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthResponse, UserLogin, UserCreate } from '@/types/api';
import { api } from '@/lib/api';
import { authStorage } from '@/utils/storage';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: UserLogin) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post<AuthResponse>('/auth/login', credentials);
          const { access_token, user } = response;
          
          // Token speichern
          authStorage.setToken(access_token);
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || error.message || 'Login fehlgeschlagen';
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null
          });
          authStorage.clearAll();
          throw new Error(errorMessage);
        }
      },

      register: async (userData: UserCreate) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post<AuthResponse>('/auth/register', userData);
          const { access_token, user } = response;
          
          // Token speichern
          authStorage.setToken(access_token);
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || error.message || 'Registrierung fehlgeschlagen';
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null
          });
          authStorage.clearAll();
          throw new Error(errorMessage);
        }
      },

      logout: () => {
        authStorage.clearAll();
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null
        });
      },

      refreshUser: async () => {
        const token = authStorage.getToken();
        if (!token) {
          set({ isAuthenticated: false, user: null, token: null });
          return;
        }

        set({ isLoading: true });
        try {
          const response = await api.get<User>('/auth/me');
          set({
            user: response,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error) {
          // Token ist ungültig, ausloggen
          authStorage.clearAll();
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          });
        }
      },

      clearError: () => set({ error: null }),
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);

// Hook für einfachen Zugriff
export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    token: store.token,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login: store.login,
    register: store.register,
    logout: store.logout,
    refreshUser: store.refreshUser,
    clearError: store.clearError,
    setLoading: store.setLoading,
  };
};

export const useAuthActions = () => {
  const store = useAuthStore();
  return {
    login: store.login,
    register: store.register,
    logout: store.logout,
    refreshUser: store.refreshUser,
    clearError: store.clearError,
    setLoading: store.setLoading,
  };
}; 