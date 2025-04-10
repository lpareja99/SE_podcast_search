// filepath: /frontend/src/Search.js
import React, { useState } from "react";

const Search = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);

    const handleSearch = async () => {
        const response = await fetch(`http://127.0.0.1:5000/search?q=${query}`);
        const data = await response.json();
        setResults(data);
    };

    return (
        <div>
            <h1>Podcast Search</h1>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for podcasts..."
            />
            <button onClick={handleSearch}>Search</button>
            <ul>
                {results.map((result, index) => (
                    <li key={index}>
                        <h3>{result.title}</h3>
                        <p>{result.description}</p>
                        <p><strong>Show:</strong> {result.show}</p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Search;