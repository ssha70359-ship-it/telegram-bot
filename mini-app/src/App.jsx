import { useEffect, useState } from 'react';
import { initTelegram, getTelegramUser } from './api';
import Onboarding from './pages/Onboarding.jsx';
import Home from './pages/Home.jsx';
import Catalog from './pages/Catalog.jsx';
import Cart from './pages/Cart.jsx';
import Profile from './pages/Profile.jsx';
import BottomNav from './components/BottomNav.jsx';
import ProductSheet from './components/ProductSheet.jsx';

export default function App() {
  const [seenOnboarding, setSeenOnboarding] = useState(
    () => localStorage.getItem('onboarding_seen') === 'true'
  );
  const [tab, setTab] = useState('home');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [user] = useState(() => getTelegramUser());

  useEffect(() => {
    initTelegram();
  }, []);

  function finishOnboarding() {
    localStorage.setItem('onboarding_seen', 'true');
    setSeenOnboarding(true);
  }

  if (!seenOnboarding) {
    return <Onboarding onFinish={finishOnboarding} />;
  }

  return (
    <div className="app">
      <div className="screen">
        {tab === 'home' && <Home user={user} onOpenCatalog={() => setTab('catalog')} />}
        {tab === 'catalog' && <Catalog onSelectProduct={setSelectedProduct} />}
        {tab === 'cart' && <Cart onDone={() => setTab('home')} />}
        {tab === 'profile' && <Profile user={user} />}
      </div>

      <BottomNav active={tab} onChange={setTab} />

      {selectedProduct && (
        <ProductSheet
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onAdded={() => {
            setSelectedProduct(null);
            setTab('catalog');
          }}
        />
      )}
    </div>
  );
}
