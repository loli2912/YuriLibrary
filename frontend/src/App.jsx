import { useEffect, useMemo, useState } from "react";
import { getItems, setRating, deleteItems } from "./api.js";
import ItemCard from "./ItemCard.jsx";

export default function App() {
  const [items, setItems] = useState([]);
  const [syncedAt, setSyncedAt] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);
  const [onlyRated, setOnlyRated] = useState(false);
  const [doujinshiFilter, setDoujinshiFilter] = useState("all"); // all | only | exclude
  const [oneshotFilter, setOneshotFilter] = useState("all"); // all | only | exclude
  const [minYear, setMinYear] = useState(""); // "" = any; otherwise year >= this
  const [search, setSearch] = useState(""); // title substring filter
  const [selected, setSelected] = useState(() => new Set()); // ids marked for bulk delete

  useEffect(() => {
    getItems()
      .then((data) => {
        setItems(data.items || []);
        setSyncedAt(data.syncedAt);
        setStatus("ready");
      })
      .catch((e) => {
        setError(e.message);
        setStatus("error");
      });
  }, []);

  async function handleRate(id, rating) {
    // Optimistic update, then persist.
    const prev = items;
    setItems((cur) =>
      cur.map((it) => (it.id === id ? { ...it, rating } : it))
    );
    try {
      await setRating(id, rating);
    } catch (e) {
      setItems(prev); // roll back on failure
      alert(`Could not save rating: ${e.message}`);
    }
  }

  function toggleSelect(id) {
    setSelected((cur) => {
      const next = new Set(cur);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleBulkDelete() {
    const ids = [...selected];
    if (ids.length === 0) return;
    // Single confirmation for the whole batch.
    if (
      !window.confirm(
        `Delete ${ids.length} selected title${ids.length > 1 ? "s" : ""}? ` +
          `They won't come back on re-sync.`
      )
    )
      return;

    const prev = items;
    const idSet = new Set(ids);
    setItems((cur) => cur.filter((it) => !idSet.has(it.id)));
    setSelected(new Set());
    try {
      await deleteItems(ids);
    } catch (e) {
      setItems(prev); // restore on failure
      setSelected(idSet);
      alert(`Could not delete: ${e.message}`);
    }
  }

  const visible = useMemo(() => {
    const minYearNum = minYear === "" ? null : Number(minYear);
    const query = search.trim().toLowerCase();
    return items.filter((it) => {
      if (query && !it.title.toLowerCase().includes(query)) return false;

      if (onlyRated && it.rating == null) return false;

      if (doujinshiFilter === "only" && !it.isDoujinshi) return false;
      if (doujinshiFilter === "exclude" && it.isDoujinshi) return false;

      if (oneshotFilter === "only" && !it.isOneshot) return false;
      if (oneshotFilter === "exclude" && it.isOneshot) return false;

      // Show titles from minYear onward. Unknown year (null) is never hidden.
      if (minYearNum != null && it.year != null && it.year < minYearNum)
        return false;

      return true;
    });
  }, [items, search, onlyRated, doujinshiFilter, oneshotFilter, minYear]);

  if (status === "loading") return <p className="msg">Loading catalog…</p>;
  if (status === "error")
    return (
      <p className="msg">
        Failed to load: {error}
        <br />
        Is the backend running, and have you run <code>python -m backend.sync</code>?
      </p>
    );

  return (
    <div className="app">
      <header className="header">
        <h1>Yuri Maker</h1>
        <p className="subtitle">
          Japanese-origin · Drama + Girls' Love · completed
        </p>
        <div className="toolbar">
          <input
            type="search"
            className="search-input"
            placeholder="Search title…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <span>{visible.length} titles</span>
          {selected.size > 0 && (
            <button className="bulk-delete" onClick={handleBulkDelete}>
              Delete selected ({selected.size})
            </button>
          )}
          <label>
            <input
              type="checkbox"
              checked={onlyRated}
              onChange={(e) => setOnlyRated(e.target.checked)}
            />
            Rated only
          </label>
          <label className="filter">
            Doujinshi:
            <select
              value={doujinshiFilter}
              onChange={(e) => setDoujinshiFilter(e.target.value)}
            >
              <option value="all">All</option>
              <option value="only">Only doujinshi</option>
              <option value="exclude">Exclude doujinshi</option>
            </select>
          </label>
          <label className="filter">
            Oneshot:
            <select
              value={oneshotFilter}
              onChange={(e) => setOneshotFilter(e.target.value)}
            >
              <option value="all">All</option>
              <option value="only">Only oneshot</option>
              <option value="exclude">Exclude oneshot</option>
            </select>
          </label>
          <label className="filter">
            From year:
            <input
              type="number"
              className="year-input"
              placeholder="any"
              min="1900"
              max="2100"
              value={minYear}
              onChange={(e) => setMinYear(e.target.value)}
            />
            {minYear !== "" && (
              <button
                type="button"
                className="clear-year"
                title="Clear year filter"
                onClick={() => setMinYear("")}
              >
                ×
              </button>
            )}
          </label>
          {syncedAt && (
            <span className="synced">
              synced {new Date(syncedAt).toLocaleString()}
            </span>
          )}
        </div>
      </header>

      <main className="grid">
        {visible.map((item) => (
          <ItemCard
            key={item.id}
            item={item}
            onRate={handleRate}
            selected={selected.has(item.id)}
            onToggleSelect={toggleSelect}
          />
        ))}
      </main>
    </div>
  );
}
