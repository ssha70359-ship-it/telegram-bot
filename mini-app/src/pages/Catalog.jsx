import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import ProductCard from '../components/ProductCard.jsx';

export default function Catalog({ onSelectProduct }) {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState('Barchasi');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getProducts()
      .then(setProducts)
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => {
    const set = new Set(products.map((p) => p.category));
    return ['Barchasi', ...set];
  }, [products]);

  const filtered = useMemo(
    () => (category === 'Barchasi' ? products : products.filter((p) => p.category === category)),
    [products, category]
  );

  return (
    <div className="page">
      <h2 className="page-title">Katalog</h2>

      <div className="category-filter">
        {categories.map((cat) => (
          <button
            key={cat}
            className={`tag ${cat === category ? 'active' : ''}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {loading && <p className="muted">Yuklanmoqda...</p>}

      <div className="product-grid">
        {filtered.map((product) => (
          <ProductCard key={product.id} product={product} onClick={onSelectProduct} />
        ))}
      </div>
    </div>
  );
}
