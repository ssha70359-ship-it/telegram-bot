import StoryBar from '../components/StoryBar.jsx';

export default function Home({ user, onOpenCatalog }) {
  return (
    <div className="page">
      <header className="header">
        <div>
          <p className="muted">Xush kelibsiz,</p>
          <h2>{user?.first_name || 'Mehmon'} 👋</h2>
        </div>
      </header>

      <StoryBar />

      <div className="hero">
        <div className="hero-emoji">🍕</div>
        <h1>Issiqqina pizza xohlaysizmi?</h1>
        <p>Eng mazali pizzalarni tez orada eshigingizga yetkazamiz.</p>
        <button className="btn-primary btn-large" onClick={onOpenCatalog}>
          Yangi buyurtma berish
        </button>
      </div>
    </div>
  );
}
