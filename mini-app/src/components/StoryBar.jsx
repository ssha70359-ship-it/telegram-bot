const stories = [
  { emoji: '🔥', label: 'Aksiya' },
  { emoji: '🍕', label: 'Menyu' },
  { emoji: '🆕', label: 'Yangi' },
  { emoji: '⭐', label: 'Reyting' },
  { emoji: '🚀', label: 'Tezkor' },
];

export default function StoryBar() {
  return (
    <div className="story-bar">
      {stories.map((story) => (
        <div className="story" key={story.label}>
          <div className="story-circle">{story.emoji}</div>
          <span>{story.label}</span>
        </div>
      ))}
    </div>
  );
}
