import { useState } from 'react';
import { useCart } from '../context/CartContext.jsx';
import { api, closeMiniApp } from '../api';

const COLA = { name: 'Kola', price: 5000 };

export default function Cart({ onDone }) {
  const { items, updateQty, removeFromCart, total, clearCart } = useCart();
  const [addCola, setAddCola] = useState(false);
  const [phone, setPhone] = useState('');
  const [location, setLocation] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const finalTotal = total + (addCola ? COLA.price : 0);

  async function handleConfirm() {
    setError('');

    if (items.length === 0) {
      setError("Savatchangiz bo'sh");
      return;
    }
    if (!phone.trim() || !location.trim()) {
      setError('Telefon raqam va manzilni kiriting');
      return;
    }

    setSubmitting(true);
    try {
      const orderItems = items.map((item) => ({
        productId: item.productId,
        name: item.name,
        price: item.price,
        qty: item.qty,
      }));

      if (addCola) {
        orderItems.push({ productId: null, name: COLA.name, price: COLA.price, qty: 1 });
      }

      await api.createOrder({
        items: orderItems,
        totalPrice: finalTotal,
        location,
        phone,
      });

      clearCart();
      closeMiniApp();
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h2 className="page-title">Savatcha</h2>

      {items.length === 0 && <p className="muted">Savatchangiz bo'sh. Katalogdan pizza tanlang!</p>}

      <div className="cart-list">
        {items.map((item) => (
          <div className="cart-item" key={item.productId}>
            <img src={item.imageUrl} alt={item.name} />
            <div className="cart-item-info">
              <h4>{item.name}</h4>
              <span>{item.price.toLocaleString()} so'm</span>
            </div>
            <div className="qty-control">
              <button onClick={() => updateQty(item.productId, item.qty - 1)}>-</button>
              <span>{item.qty}</span>
              <button onClick={() => updateQty(item.productId, item.qty + 1)}>+</button>
            </div>
            <button className="remove-btn" onClick={() => removeFromCart(item.productId)}>
              ✕
            </button>
          </div>
        ))}
      </div>

      {items.length > 0 && (
        <>
          <div className="upsell">
            <span>Bunga qo'shimcha ravishda Kola'ni atigi 5,000 so'mga qo'shasizmi?</span>
            <label className="switch">
              <input type="checkbox" checked={addCola} onChange={(e) => setAddCola(e.target.checked)} />
              <span className="slider" />
            </label>
          </div>

          <div className="form-group">
            <label>Yetkazish manzili</label>
            <input
              type="text"
              placeholder="Ko'cha, uy raqami..."
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Telefon raqam</label>
            <input
              type="tel"
              placeholder="+998 90 123 45 67"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <div className="cart-total">
            <span>Jami:</span>
            <strong>{finalTotal.toLocaleString()} so'm</strong>
          </div>

          <button className="btn-primary btn-large sticky-cta" onClick={handleConfirm} disabled={submitting}>
            {submitting ? 'Yuborilmoqda...' : 'Buyurtmani tasdiqlash'}
          </button>
        </>
      )}
    </div>
  );
}
