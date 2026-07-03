import { useState } from "react";

const RATINGS = Array.from({ length: 11 }, (_, i) => i); // 0..10

export default function ItemCard({ item, onRate, selected, onToggleSelect }) {
  const [imgError, setImgError] = useState(false);

  return (
    <article className={`card${selected ? " selected" : ""}`}>
      <div className="cover">
        <label className="select-box" title="Select for bulk delete">
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onToggleSelect(item.id)}
          />
        </label>
        {item.coverUrl && !imgError ? (
          <img
            src={item.coverUrl}
            alt={item.title}
            loading="lazy"
            // Some MangaDex covers 403 on hotlink with a referer header.
            referrerPolicy="no-referrer"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="cover-fallback">No cover</div>
        )}
      </div>

      <h2 className="title" title={item.title}>
        {item.title}
      </h2>

      <div className="rating">
        <select
          value={item.rating ?? ""}
          onChange={(e) => onRate(item.id, Number(e.target.value))}
        >
          <option value="" disabled>
            Rate…
          </option>
          {RATINGS.map((n) => (
            <option key={n} value={n}>
              {n} / 10
            </option>
          ))}
        </select>
        {item.rating != null && <span className="badge">{item.rating}</span>}
      </div>
    </article>
  );
}
