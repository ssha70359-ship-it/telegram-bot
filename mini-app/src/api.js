const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000';

function getTelegram() {
  return window.Telegram?.WebApp;
}

async function request(path, options = {}) {
  const tg = getTelegram();
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  if (tg?.initData) {
    headers['x-telegram-init-data'] = tg.initData;
  }

  let body = options.body;
  if (body && typeof body === 'object') {
    if (tg?.initDataUnsafe?.user) {
      body.telegramUser = tg.initDataUnsafe.user;
    }
    body = JSON.stringify(body);
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers, body });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Xatolik yuz berdi' }));
    throw new Error(err.error || 'Xatolik yuz berdi');
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getProducts: () => request('/api/client/products'),
  getProduct: (id) => request(`/api/client/products/${id}`),
  syncUser: (phone) => request('/api/client/user/sync', { method: 'POST', body: { phone } }),
  getMyOrders: () => request('/api/client/orders'),
  createOrder: (payload) => request('/api/client/orders', { method: 'POST', body: payload }),
};

export function getTelegramUser() {
  return getTelegram()?.initDataUnsafe?.user || null;
}

export function closeMiniApp() {
  getTelegram()?.close();
}

export function initTelegram() {
  const tg = getTelegram();
  if (tg) {
    tg.ready();
    tg.expand();
  }
}
