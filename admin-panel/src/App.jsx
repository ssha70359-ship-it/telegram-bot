import { useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Orders from './pages/Orders.jsx';
import Products from './pages/Products.jsx';

export default function App() {
  const [page, setPage] = useState('orders');

  return (
    <div className="layout">
      <Sidebar page={page} onChange={setPage} />
      <main className="content">{page === 'orders' ? <Orders /> : <Products />}</main>
    </div>
  );
}
