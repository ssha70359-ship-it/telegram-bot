import { useState } from 'react';

const slides = [
  {
    emoji: '😋',
    title: 'Sizni ochlik qiynayaptimi?',
    text: 'Biz issiqqina pizzalarni tezkor yetkazamiz.',
  },
  {
    emoji: '📱',
    title: 'Bu qanday ishlaydi?',
    text: 'Tanlang, buyurtma bering va rohatlaning.',
  },
  {
    emoji: '🎉',
    title: '10,000+ odam',
    text: 'Allaqachon biz bilan buyurtma qilmoqda.',
  },
];

export default function Onboarding({ onFinish }) {
  const [index, setIndex] = useState(0);
  const isLast = index === slides.length - 1;
  const slide = slides[index];

  return (
    <div className="onboarding">
      <div className="onboarding-emoji">{slide.emoji}</div>
      <h1>{slide.title}</h1>
      <p>{slide.text}</p>

      <div className="dots">
        {slides.map((_, i) => (
          <span key={i} className={`dot ${i === index ? 'active' : ''}`} />
        ))}
      </div>

      <button
        className="btn-primary btn-large"
        onClick={() => (isLast ? onFinish() : setIndex(index + 1))}
      >
        {isLast ? 'Boshla' : 'Keyingisi'}
      </button>
    </div>
  );
}
