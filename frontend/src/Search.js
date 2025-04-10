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
        <div className="container mt-5">
            <h1 className="text-center mb-4">Podcast Search</h1>
            <div className="row justify-content-center">
                <div className="col-md-6">
                    <input
                        type="text"
                        className="form-control mb-3"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for podcasts..."
                    />
                    <button className="btn btn-primary w-100" onClick={handleSearch}>
                        Search
                    </button>
                </div>
            </div>
            <ul className="list-group mt-4">
                {results.map((result, index) => (
                    <li key={index} className="list-group-item">
                        <h5>{result.title}</h5>
                        <p>{result.description}</p>
                        <p>
                            <strong>Show:</strong> {result.show}
                        </p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Search;