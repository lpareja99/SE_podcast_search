import React, { useState } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import "./search.css";
import { API_BASE_URL, SEARCH_FILTERS, SEARCH_TYPES, RANKING_TYPES, TIME_RANGE_INTERVALS } from "./config";

const Search = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [selectedShow, setSelectedShow] = useState(null);
    const [checkedEpisodes, setCheckedEpisodes] = useState([]);
    const [searchType, setSearchType] = useState("Intersection");
    const [rankingType, setRankingType] = useState("Pagerank");
    const [timeRange, setTimeRange] = useState(1); 
    const [isAccordionOpen, setIsAccordionOpen] = useState(false);
    const [selectedTag, setSelectedTag] = useState("General");

    const handleSearch = async () => {
        const params = new URLSearchParams({
            q: query,
            filter: selectedTag,
            type: searchType,
            ranking: searchType === "Ranking" ? rankingType : undefined,
            time: timeRange,
            selectedEpisodes: checkedEpisodes.join(","),
        });
        console.log("Search Parameters:", Object.fromEntries(params.entries()));
        const response = await fetch(`${API_BASE_URL}/search?${params}`);
        const data = await response.json();

        if (!Array.isArray(data)) {
            console.error("Unexpected API response format:", data);
            setResults([]); // Clear results if the response is not an array
            return;
        }

        const resultsWithIds = data.map((result, index) => ({
            ...result,
            id: result.id || index,
        }));

        setResults(resultsWithIds);
    };

    const handleCheckboxChange = (episodeId) => {
        setCheckedEpisodes((prev) => {
            const isChecked = prev.includes(episodeId);
            return isChecked ? prev.filter((id) => id !== episodeId) : [...prev, episodeId];
        });
    };
    
    return (
        <div className="container mt-5 search-container">
            <h1 className="text-center mb-4 podcast-title">Advanced Podcast Search</h1>

            <div className="d-flex gap-2 mb-2">
                {SEARCH_FILTERS.map((tag) => (
                    <button
                        key={tag}
                        className={`btn ${selectedTag === tag ? "btn-secondary" : "btn-outline-secondary"} text-small`}
                        onClick={() => setSelectedTag(tag)}
                    >
                        {tag}
                    </button>
                ))}
            </div>

            <div className="d-flex align-items-center gap-2 mb-3 ">
                <input
                    type="text"
                    className="form-control search-bar search-bar-large"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search for podcasts..."
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            handleSearch();
                        }
                    }}
                />
                <button className="btn search-icon-btn" onClick={handleSearch}>
                    <i className="bi bi-search"></i>
                </button>
            </div>

            <div className="accordion" id="advancedSearchAccordion">
                <div className="accordion-item">
                    <h2 className="accordion-header" id="headingOne">
                        <button
                            className={`accordion-button ${isAccordionOpen ? "" : "collapsed"}`}
                            type="button"
                            onClick={() => setIsAccordionOpen(!isAccordionOpen)}
                            aria-expanded={isAccordionOpen}
                            aria-controls="collapseOne"
                        >
                            Advanced Search
                        </button>
                    </h2>
                    <div
                        id="collapseOne"
                        className={`accordion-collapse collapse ${isAccordionOpen ? "show" : ""}`}
                        aria-labelledby="headingOne"
                        data-bs-parent="#advancedSearchAccordion"
                    >
                        <div className="accordion-body">
                                <div className="d-flex gap-2 justify-content-center">
                                    <div className="col-4 text-center">
                                        <label className="form-label secondary-text">Search Type</label>
                                        <div className="d-flex justify-content-center filter-block gap-1">
                                            {SEARCH_TYPES.map((type) => (
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
                                    <div className="col-4 text-center">
                                        <label className="form-label secondary-text">Ranking Type</label>
                                        <div className="d-flex justify-content-center filter-block gap-1">
                                            {RANKING_TYPES.map((type) => (
                                                <button
                                                    key={type}
                                                    className={`btn ranking-tag-btn ${rankingType === type ? "selected-ranking-tag" : ""}`}
                                                    onClick={() => searchType === "Ranking" && setRankingType(type)}
                                                    disabled={searchType !== "Ranking"} 
                                                >
                                                    {type.charAt(0).toUpperCase() + type.slice(1)}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="col-4 text-center">
                                        <label className="form-label secondary-text">Time Range (Minutes)</label>
                                        <input
                                            type="range"
                                            className="form-range"
                                            min={0}
                                            max={TIME_RANGE_INTERVALS.length - 1}
                                            step={1}
                                            value={TIME_RANGE_INTERVALS.indexOf(timeRange)}
                                            onChange={(e) => setTimeRange(TIME_RANGE_INTERVALS[parseInt(e.target.value)])}
                                        />
                                        <div className="d-flex justify-content-between small text-muted">
                                            {TIME_RANGE_INTERVALS.map((interval, index) => (
                                                <span key={index}>
                                                    {interval === 0.5 ? "30 sec" : `${interval} min`}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                        </div>
                    </div>
                </div>
            </div>
            <div className="row mt-4">
                <div className="col-md-4">
                    <div className="list-group">
                        {results.map((result, index) => (
                            <div
                                key={index}
                                className={`list-group-item list-group-item-action mb-2 rounded podcast-item d-flex align-items-start ${
                                    selectedShow === result ? "selected-item" : ""
                                }`}
                                onClick={() => setSelectedShow(result)}
                            >
                                <input
                                    type="checkbox"
                                    className="episode-checkbox"
                                    checked={checkedEpisodes.includes(result.id)}
                                    onChange={(e) => {
                                        e.stopPropagation();
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