const items = [
  { key: 'orders', label: 'Buyurtmalar', icon: '📦' },
  { key: 'products', label: 'Mahsulotlar', icon: '🍕' },
];

export default function Sidebar({ page, onChange }) {
  return (
    <aside className="sidebar">
      <div className="brand">🍕 Pizza Admin</div>
      <nav>
        {items.map((item) => (
          <button
            key={item.key}
            className={`sidebar-item ${page === item.key ? 'active' : ''}`}
            onClick={() => onChange(item.key)}
          >
            <span>{item.icon}</span> {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
