// filepath: /frontend/src/Search.js
import React, { useState } from "react";
// Import bootstrap first, then your CSS
import 'bootstrap/dist/css/bootstrap.min.css';
// Make sure this matches exactly with your file name (case sensitive)
import "./search.css";  

const Search = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [selectedShow, setSelectedShow] = useState(null);
    const [checkedEpisodes, setCheckedEpisodes] = useState([]);
    const [searchType, setSearchType] = useState("intersection");
    const [rankingType, setRankingType] = useState("relevance");
    const [timeRange, setTimeRange] = useState(1); 

    const handleSearch = async () => {
        const params = new URLSearchParams({
            q: query,
            type: searchType,
            ranking: searchType === "ranking" ? rankingType : undefined,
            time: timeRange,
        });
        const response = await fetch(`http://127.0.0.1:5000/search?${params}`);
        const data = await response.json();
        setResults(data);
    };

    const handleCheckboxChange = (episodeId) => {
        setCheckedEpisodes((prev) =>
            prev.includes(episodeId)
                ? prev.filter((id) => id !== episodeId) // Remove if already checked
                : [...prev, episodeId] // Add if not checked
        );
    };
    
    return (
        <div className="container mt-5 search-container">
            <h1 className="text-center mb-4 podcast-title">Advanced Podcast Search</h1>

            <div className="row justify-content-center">
                <div className="">
                    <div className="search-controls p-4 rounded shadow-sm bg-white">

                        {/* Search Input Row */}
                        <div className="d-flex align-items-center gap-2 mb-4">
                            <input
                                type="text"
                                className="form-control search-bar"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Search for podcasts..."
                            />
                            <button className="btn search-icon-btn" onClick={handleSearch}>
                                <i className="bi bi-search"></i>
                            </button>
                        </div>

                        {/* Filters Row */}
                        <div className="d-flex gap-2 justify-content-center">
                            {/* Search Type */}
                            <div className="col-4 text-center">
                                <label className="form-label secondary-text">Search Type</label>
                                <div className="d-flex justify-content-center filter-block gap-1">
                                    {["intersection", "phrase", "ranking"].map((type) => (
                                        <button
                                            key={type}
                                            className={`btn tag-btn ${searchType === type ? "selected-tag" : ""}`}
                                            onClick={() => setSearchType(type)}
                                        >
                                            {type.charAt(0).toUpperCase() + type.slice(1)}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Ranking Type (only if needed) */}
                            {searchType === "ranking" && (
                                <div className="col-4 text-center">
                                    <label className="form-label secondary-text">Ranking Type</label>
                                    <div className="d-flex justify-content-center filter-block gap-1">
                                        {["relevance", "popularity", "date"].map((type) => (
                                            <button
                                                key={type}
                                                className={`btn ranking-tag-btn ${rankingType === type ? "selected-ranking-tag" : ""}`}
                                                onClick={() => setRankingType(type)}
                                            >
                                                {type.charAt(0).toUpperCase() + type.slice(1)}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Time Range */}
                            <div className="col-4 text-center">
                                <label className="form-label secondary-text">Time Range (Minutes)</label>
                                <input
                                    type="range"
                                    className="form-range"
                                    min="0.5"
                                    max="5"
                                    step="0.5"
                                    value={timeRange}
                                    onChange={(e) => setTimeRange(parseFloat(e.target.value))}
                                />
                                <div className="d-flex justify-content-between small text-muted">
                                    <span>30 sec</span>
                                    <span>1 min</span>
                                    <span>1:30</span>
                                    <span>2 min</span>
                                    <span>3 min</span>
                                    <span>5 min</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="row mt-4">
                {/* Left Section: List of Shows */}
                <div className="col-md-4">
                    <div className="list-group">
                        {results.map((result, index) => (
                            <div
                                key={index}
                                className={`list-group-item list-group-item-action mb-2 rounded podcast-item d-flex align-items-start ${
                                    selectedShow === result ? 'selected-item' : ''
                                }`}
                                onClick={() => setSelectedShow(result)}
                            >
                                <input
                                    type="checkbox"
                                    className="episode-checkbox"
                                    checked={checkedEpisodes.includes(result.id)}
                                    onChange={(e) => {
                                        e.stopPropagation(); // Prevent triggering the card click
                                        handleCheckboxChange(result.id);
                                    }}
                                />
                                <div className="rank-badge me-3">{index + 1}</div>
                                <div>
                                    <h5 className="mb-1 podcast-title">{result.show}</h5>
                                    <p className="mb-1 episode-info">
                                        <strong>Episode:</strong> {result.title}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                
                {/* Right Section: Selected Show Details */}
                <div className="col-md-8">
                    {selectedShow ? (
                        <div className="card rounded custom-card">
                            <div className="card-body">
                                <h5 className="card-title podcast-title">{selectedShow.show}</h5>
                                <p className="card-text main-text">{selectedShow.description}</p>
                                <p className="card-text episode-info">
                                    <strong>Episode:</strong> {selectedShow.title}
                                </p>
                            </div>
                        </div>
                    ) : (
                        results.length > 0 && (
                            <p className="text-center secondary-text">Select a show to see details</p>
                        )
                    )}
                </div>
            </div>
        </div>
    );
};

export default Search;