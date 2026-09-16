const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000';

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  let body = options.body;
  if (body && typeof body === 'object') {
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
  getOrders: () => request('/api/admin/orders'),
  updateOrderStatus: (id, status) =>
    request(`/api/admin/orders/${id}/status`, { method: 'PATCH', body: { status } }),

  getProducts: () => request('/api/admin/products'),
  createProduct: (data) => request('/api/admin/products', { method: 'POST', body: data }),
  updateProduct: (id, data) => request(`/api/admin/products/${id}`, { method: 'PUT', body: data }),
  deleteProduct: (id) => request(`/api/admin/products/${id}`, { method: 'DELETE' }),
};
