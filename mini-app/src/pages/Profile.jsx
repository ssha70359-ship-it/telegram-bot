import { useEffect, useState } from 'react';
import { api } from '../api';
import { useCart } from '../context/CartContext.jsx';

const STATUS_LABELS = {
  kutilmoqda: '⏳ Kutilmoqda',
  yetkazildi: '✅ Yetkazildi',
  bekor_qilindi: '❌ Bekor qilindi',
};

export default function Profile({ user }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToCart } = useCart();

  useEffect(() => {
    api
      .getMyOrders()
      .then(setOrders)
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, []);

  function reorder(order) {
    const items = Array.isArray(order.items) ? order.items : [];
    items.forEach((item) => {
      if (!item.productId) return;
      addToCart(
        { id: item.productId, name: item.name, newPrice: item.price, imageUrl: item.imageUrl },
        item.qty
      );
    });
  }

  return (
    <div className="page">
      <h2 className="page-title">Profil</h2>

      <div className="profile-card">
        <div className="avatar">{user?.first_name?.[0] || '👤'}</div>
        <div>
          <h3>{user?.first_name || 'Mehmon'} {user?.last_name || ''}</h3>
          <p className="muted">@{user?.username || 'foydalanuvchi'}</p>
        </div>
      </div>

      <h3 className="section-title">📜 Mening buyurtmalarim</h3>

      {loading && <p className="muted">Yuklanmoqda...</p>}
      {!loading && orders.length === 0 && <p className="muted">Hali buyurtmalar yo'q</p>}

      <div className="order-list">
        {orders.map((order) => (
          <div className="order-card" key={order.id}>
            <div className="order-header">
              <span>{new Date(order.createdAt).toLocaleDateString('uz-UZ')}</span>
              <span className="status">{STATUS_LABELS[order.status] || order.status}</span>
            </div>
            <ul>
              {(Array.isArray(order.items) ? order.items : []).map((item, i) => (
                <li key={i}>
                  {item.name} x{item.qty}
                </li>
              ))}
            </ul>
            <div className="order-footer">
              <strong>{order.totalPrice.toLocaleString()} so'm</strong>
              <button className="btn-secondary" onClick={() => reorder(order)}>
                Yana shundan buyurtma qilish
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
