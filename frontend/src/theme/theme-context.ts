import { createContext } from 'react'

export type Theme = 'light' | 'dark'

export interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
}

export const themeStorageKey = 'pyexplorer-theme'
export const ThemeContext = createContext<ThemeContextValue | null>(null)
