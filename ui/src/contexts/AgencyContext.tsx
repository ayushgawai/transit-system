import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getApiBaseUrl } from '../utils/api'

type Agency = 'BART' | 'VTA' | 'All'

interface AgencyContextType {
  agency: Agency
  setAgency: (agency: Agency) => void
  availableAgencies: Agency[]
}

const AgencyContext = createContext<AgencyContextType | undefined>(undefined)

export function AgencyProvider({ children }: { children: ReactNode }) {
  const [agency, setAgencyState] = useState<Agency>('BART')
  const [availableAgencies, setAvailableAgencies] = useState<Agency[]>(['BART', 'VTA'])

  // Load agency from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('selectedAgency') as Agency
    if (saved && (saved === 'BART' || saved === 'VTA' || saved === 'All')) {
      setAgencyState(saved)
    }
  }, [])

  // Fetch available agencies from API
  useEffect(() => {
    fetch(`${getApiBaseUrl()}/agencies`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data && data.data.length > 0) {
          const agencies: Agency[] = ['All', ...data.data.filter((a: string) => a === 'BART' || a === 'VTA')] as Agency[]
          setAvailableAgencies(agencies)
        }
      })
      .catch(err => console.error('Failed to fetch agencies:', err))
  }, [])

  const setAgency = (newAgency: Agency) => {
    setAgencyState(newAgency)
    localStorage.setItem('selectedAgency', newAgency)
  }

  return (
    <AgencyContext.Provider value={{ agency, setAgency, availableAgencies }}>
      {children}
    </AgencyContext.Provider>
  )
}

export function useAgency() {
  const context = useContext(AgencyContext)
  if (context === undefined) {
    throw new Error('useAgency must be used within an AgencyProvider')
  }
  return context
}

