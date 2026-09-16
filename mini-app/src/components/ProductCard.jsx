import { useCart } from '../context/CartContext.jsx';

export default function ProductCard({ product, onClick }) {
  const { addToCart } = useCart();

  return (
    <div className="product-card" onClick={() => onClick(product)}>
      <img src={product.imageUrl} alt={product.name} className="product-image" />
      <button
        className="quick-add"
        onClick={(e) => {
          e.stopPropagation();
          addToCart(product, 1);
        }}
      >
        ➕
      </button>
      <div className="product-info">
        <h3>{product.name}</h3>
        <div className="price-row">
          {product.oldPrice && <span className="old-price">{product.oldPrice.toLocaleString()} so'm</span>}
          <span className="new-price">{product.newPrice.toLocaleString()} so'm</span>
        </div>
      </div>
    </div>
  );
}
