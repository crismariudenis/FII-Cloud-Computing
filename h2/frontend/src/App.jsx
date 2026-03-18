import { useState } from "react";

function App() {
  const [city, setCity] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newNote, setNewNote] = useState("");

  const fetchData = async (e) => {
    if (e) e.preventDefault();
    if (!city) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/dashboard/${city}`,
      );
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Failed to fetch data from backend");
      }

      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote) return;

    // Optimistic UI update could be done here, but let's wait for server response
    try {
      const response = await fetch(`http://localhost:8000/api/notes/${city}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: newNote }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert("Failed to add note: " + (errorData.detail || "Unknown error"));
        return;
      }

      setData((prevData) => ({
        ...prevData,
        local_notes: [...(prevData.local_notes || []), newNote],
      }));
      setNewNote("");
    } catch (err) {
      alert("Error connecting to server: " + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-extrabold mb-8 text-slate-800 text-center">
          City Explorer Dashboard
        </h1>

        {/* Search Bar */}
        <form
          onSubmit={fetchData}
          className="mb-8 flex gap-4 max-w-2xl mx-auto"
        >
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter a city (e.g., Tokyo, Paris, Iasi)"
            className="p-3 border border-slate-300 rounded-lg shadow-sm flex-grow outline-none focus:ring-2 focus:ring-blue-500 text-lg"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg shadow-md hover:bg-blue-700 disabled:opacity-50 font-semibold transition-colors"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-8 border border-red-200 text-center max-w-2xl mx-auto">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results Grid */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 1. HW1 Service Card (My Notes) */}
            <div className="bg-white p-6 rounded-xl shadow-md border-t-4 border-indigo-500 hover:shadow-lg transition-shadow flex flex-col h-full">
              <h2 className="text-xl font-bold mb-4 text-slate-700 border-b pb-2">
                My Notes (HW1)
              </h2>

              <div className="flex-grow overflow-y-auto max-h-60 mb-4 pr-2">
                {data.local_notes && data.local_notes.length > 0 ? (
                  <ul className="space-y-2">
                    {data.local_notes.map((note, idx) => (
                      <li
                        key={idx}
                        className="bg-slate-100 p-2 rounded text-slate-700 text-sm border border-slate-200 break-words"
                      >
                        {note}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 italic text-center text-sm mt-4">
                    No notes yet.
                  </p>
                )}
              </div>

              <form
                onSubmit={handleAddNote}
                className="mt-auto pt-2 border-t border-slate-100 flex gap-2"
              >
                <input
                  type="text"
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Add a new note..."
                  className="flex-grow p-2 text-sm border rounded focus:ring-2 focus:ring-indigo-500 outline-none"
                />
                <button
                  type="submit"
                  className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 transition"
                >
                  Add
                </button>
              </form>
            </div>

            {/* 2. Weather Service Card */}
            <div className="bg-white p-6 rounded-xl shadow-md border-t-4 border-sky-400 hover:shadow-lg transition-shadow h-full">
              <h2 className="text-xl font-bold mb-4 text-slate-700 border-b pb-2">
                Current Weather
              </h2>
              <div className="text-center mt-6">
                <p className="text-5xl font-black text-slate-800">
                  {Math.round(data.weather.main.temp)}°C
                </p>
                <p className="capitalize text-slate-500 mt-2 text-lg">
                  {data.weather.weather[0].description}
                </p>
                <div className="flex justify-center gap-4 mt-6 text-sm text-slate-500">
                  <p>
                    Humidity:{" "}
                    <span className="font-semibold">
                      {data.weather.main.humidity}%
                    </span>
                  </p>
                  <p>
                    Wind:{" "}
                    <span className="font-semibold">
                      {data.weather.wind.speed} m/s
                    </span>
                  </p>
                </div>
              </div>
            </div>

            {/* 3. News Service Card */}
            <div className="bg-white p-6 rounded-xl shadow-md border-t-4 border-emerald-500 hover:shadow-lg transition-shadow h-full flex flex-col">
              <h2 className="text-xl font-bold mb-4 text-slate-700 border-b pb-2">
                Latest News
              </h2>
              <div className="text-sm space-y-4 overflow-y-auto flex-grow max-h-96 pr-2">
                {data.news.map((article, index) => (
                  <div key={index} className="group">
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-600 group-hover:text-emerald-800 font-semibold line-clamp-2 hover:underline"
                    >
                      {article.title}
                    </a>
                    <span className="text-xs text-slate-400 block mt-1">
                      {new Date(article.publishedAt).toLocaleDateString()}
                    </span>
                  </div>
                ))}
                {data.news.length === 0 && (
                  <p className="text-slate-500 italic">
                    No recent news found for this location.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
