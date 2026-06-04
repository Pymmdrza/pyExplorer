import './App.css'

import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { AddressPage } from './pages/AddressPage'
import { BlockPage } from './pages/BlockPage'
import { DashboardPage } from './pages/DashboardPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { TransactionPage } from './pages/TransactionPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="transactions/:txHash" element={<TransactionPage />} />
          <Route path="addresses/:address" element={<AddressPage />} />
          <Route path="blocks/:height" element={<BlockPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
