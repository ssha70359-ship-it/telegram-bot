import { useCart } from '../context/CartContext.jsx';

const tabs = [
  { key: 'home', label: 'Bosh sahifa', icon: '🏠' },
  { key: 'catalog', label: 'Katalog', icon: '🔍' },
  { key: 'cart', label: 'Savatcha', icon: '🛒' },
  { key: 'profile', label: 'Profil', icon: '👤' },
];

export default function BottomNav({ active, onChange }) {
  const { count } = useCart();

  return (
    <nav className="bottom-nav">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={`nav-item ${active === tab.key ? 'active' : ''}`}
          onClick={() => onChange(tab.key)}
        >
          <span className="nav-icon">
            {tab.icon}
            {tab.key === 'cart' && count > 0 && <span className="badge">{count}</span>}
          </span>
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
