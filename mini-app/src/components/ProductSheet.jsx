import { useCart } from '../context/CartContext.jsx';

export default function ProductSheet({ product, onClose, onAdded }) {
  const { addToCart } = useCart();

  const ingredients = (product.description || '')
    .split(/[,.]/)
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div className="sheet-overlay" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-handle" />
        <img src={product.imageUrl} alt={product.name} className="sheet-image" />

        <div className="sheet-body">
          <h2>{product.name}</h2>

          {ingredients.length > 0 && (
            <ul className="ingredients">
              {ingredients.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          )}
        </div>

        <button
          className="btn-primary btn-large sticky-cta"
          onClick={() => {
            addToCart(product, 1);
            onAdded();
          }}
        >
          Savatchaga qo'shish — {product.newPrice.toLocaleString()} so'm
        </button>
      </div>
    </div>
  );
}
