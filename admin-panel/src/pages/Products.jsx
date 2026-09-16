import { useEffect, useState } from 'react';
import { api } from '../api';
import ProductModal from '../components/ProductModal.jsx';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [showModal, setShowModal] = useState(false);

  function load() {
    setLoading(true);
    api
      .getProducts()
      .then(setProducts)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  function openCreate() {
    setEditing(null);
    setShowModal(true);
  }

  function openEdit(product) {
    setEditing(product);
    setShowModal(true);
  }

  async function handleSave(form) {
    if (editing) {
      await api.updateProduct(editing.id, form);
    } else {
      await api.createProduct(form);
    }
    setShowModal(false);
    load();
  }

  async function handleDelete(id) {
    if (!confirm("Bu mahsulotni o'chirishga ishonchingiz komilmi?")) return;
    await api.deleteProduct(id);
    load();
  }

  return (
    <div>
      <div className="page-header">
        <h1>Mahsulotlar</h1>
        <button className="btn-primary" onClick={openCreate}>
          + Yangi pizza
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rasm</th>
              <th>Nomi</th>
              <th>Kategoriya</th>
              <th>Eski narx</th>
              <th>Yangi narx</th>
              <th>Amallar</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td>
                  <img src={product.imageUrl} alt={product.name} className="thumb" />
                </td>
                <td>{product.name}</td>
                <td>{product.category}</td>
                <td>{product.oldPrice ? `${product.oldPrice.toLocaleString()} so'm` : '-'}</td>
                <td>{product.newPrice.toLocaleString()} so'm</td>
                <td className="actions">
                  <button className="btn-outline" onClick={() => openEdit(product)}>
                    Tahrirlash
                  </button>
                  <button className="btn-danger" onClick={() => handleDelete(product.id)}>
                    O'chirish
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && products.length === 0 && <p className="empty">Mahsulotlar topilmadi</p>}
        {loading && <p className="empty">Yuklanmoqda...</p>}
      </div>

      {showModal && (
        <ProductModal product={editing} onClose={() => setShowModal(false)} onSave={handleSave} />
      )}
    </div>
  );
}
