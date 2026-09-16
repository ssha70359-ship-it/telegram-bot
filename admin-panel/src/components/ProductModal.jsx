import { useState } from 'react';

const empty = {
  name: '',
  description: '',
  imageUrl: '',
  oldPrice: '',
  newPrice: '',
  category: '',
};

export default function ProductModal({ product, onClose, onSave }) {
  const [form, setForm] = useState(product ? { ...empty, ...product } : empty);
  const [saving, setSaving] = useState(false);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(form);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{product ? 'Mahsulotni tahrirlash' : 'Yangi mahsulot'}</h2>

        <label>Nomi</label>
        <input required value={form.name} onChange={(e) => update('name', e.target.value)} />

        <label>Ta'rifi</label>
        <textarea value={form.description || ''} onChange={(e) => update('description', e.target.value)} />

        <label>Rasm URL</label>
        <input value={form.imageUrl || ''} onChange={(e) => update('imageUrl', e.target.value)} />

        <label>Kategoriyasi</label>
        <input required value={form.category} onChange={(e) => update('category', e.target.value)} />

        <div className="form-row">
          <div>
            <label>Eski narxi</label>
            <input
              type="number"
              value={form.oldPrice || ''}
              onChange={(e) => update('oldPrice', e.target.value)}
            />
          </div>
          <div>
            <label>Yangi narxi</label>
            <input
              required
              type="number"
              value={form.newPrice || ''}
              onChange={(e) => update('newPrice', e.target.value)}
            />
          </div>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn-outline" onClick={onClose}>
            Bekor qilish
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saqlanmoqda...' : 'Saqlash'}
          </button>
        </div>
      </form>
    </div>
  );
}
