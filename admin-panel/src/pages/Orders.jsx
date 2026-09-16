import { useEffect, useState } from 'react';
import { api } from '../api';

const STATUS_OPTIONS = ['kutilmoqda', 'yetkazildi', 'bekor_qilindi'];

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .getOrders()
      .then(setOrders)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleStatusChange(id, status) {
    await api.updateOrderStatus(id, status);
    load();
  }

  return (
    <div>
      <div className="page-header">
        <h1>Buyurtmalar</h1>
        <button className="btn-outline" onClick={load}>
          🔄 Yangilash
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Mijoz</th>
              <th>Telefon</th>
              <th>Mahsulotlar</th>
              <th>Manzil</th>
              <th>Jami</th>
              <th>Sana</th>
              <th>Holati</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id}>
                <td>#{order.id}</td>
                <td>
                  {order.user?.firstName} {order.user?.lastName || ''}
                </td>
                <td>{order.user?.phone || '-'}</td>
                <td>
                  {(Array.isArray(order.items) ? order.items : [])
                    .map((item) => `${item.name} x${item.qty}`)
                    .join(', ')}
                </td>
                <td>{order.location || '-'}</td>
                <td>{order.totalPrice.toLocaleString()} so'm</td>
                <td>{new Date(order.createdAt).toLocaleString('uz-UZ')}</td>
                <td>
                  <select value={order.status} onChange={(e) => handleStatusChange(order.id, e.target.value)}>
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && orders.length === 0 && <p className="empty">Hozircha buyurtmalar yo'q</p>}
        {loading && <p className="empty">Yuklanmoqda...</p>}
      </div>
    </div>
  );
}
