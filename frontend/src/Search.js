import React, { useState } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import "./search.css";
import { API_BASE_URL, SEARCH_FILTERS, SEARCH_TYPES, RANKING_TYPES } from "./config";

const TIME_RANGE_INTERVALS = [
    { label: "30 sec", value: 30 },
    { label: "1 min", value: 60 },
    { label: "2 min", value: 120 },
    { label: "3 min", value: 180 },
    { label: "5 min", value: 300 },
];

const FILTER_MAPPING = [
    {label: "General", value: 'general'},
    {label: "Show", value: 'show_name'},
    {label: "Author", value: 'publisher'},
    {label: "Episode", value: 'episode_title'},
]

const Search = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [selectedShow, setSelectedShow] = useState(null);
    const [checkedEpisodes, setCheckedEpisodes] = useState([]);
    const [searchType, setSearchType] = useState("Intersection");
    const [rankingType, setRankingType] = useState("Pagerank");
    const [timeRange, setTimeRange] = useState(TIME_RANGE_INTERVALS[0]); 
    const [isAccordionOpen, setIsAccordionOpen] = useState(false);
    const [selectedTag, setSelectedTag] = useState(FILTER_MAPPING[0].value);
    const [isLoading, setIsLoading] = useState(false);

    const handleSearch = async () => {
        setIsLoading(true);
        const params = new URLSearchParams({
            q: query,
            filter: selectedTag,
            type: searchType,
            ranking: searchType === "Ranking" ? rankingType : undefined,
            time: timeRange.value,
            selectedEpisodes: checkedEpisodes.join(","),
        });
        console.log("Search Parameters:", Object.fromEntries(params.entries()));
        try {
            const response = await fetch(`${API_BASE_URL}/search?${params}`);
            const data = await response.json();

            if (!Array.isArray(data)) {
                console.error("Unexpected API response format:", data);
                setResults([]);
                return;
            }

            const resultsWithIds = data.map((result, index) => ({
                ...result,
                id: result.id || index,
            }));

            setResults(resultsWithIds);
        } catch (error) {
            console.error("Error fetching search results:", error);
            setResults([]);
        } finally {
            setIsLoading(false); // Set loading to false after the API call
        }
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
                {FILTER_MAPPING.map((filter) => (
                    <button
                        key={filter.value}
                        className={`btn ${selectedTag === filter.value ? "btn-secondary" : "btn-outline-secondary"} text-small`}
                        onClick={() => setSelectedTag(filter.value)}
                    >
                        {filter.label}
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
                                        <label className="form-label secondary-text">Time Range</label>
                                        <input
                                            type="range"
                                            className="form-range"
                                            min={0}
                                            max={TIME_RANGE_INTERVALS.length - 1}
                                            step={1}
                                            value={TIME_RANGE_INTERVALS.findIndex((interval) => interval.value === timeRange.value)}
                                            onChange={(e) => setTimeRange(TIME_RANGE_INTERVALS[parseInt(e.target.value)])}
                                        />
                                        <div className="d-flex justify-content-between small text-muted">
                                            {TIME_RANGE_INTERVALS.map((interval, index) => (
                                                <span key={index}>{interval.label}</span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                        </div>
                    </div>
                </div>
            </div>
            {isLoading ? ( // Show loading spinner or message while loading
                <div className="text-center mt-4">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                </div>
            ) : (
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
                                    checked={checkedEpisodes.includes(result.metadata?.episode_id)}
                                    onChange={(e) => {
                                        e.stopPropagation();
                                        handleCheckboxChange(result.metadata?.episode_id);
                                    }}
                                />
                                <div className="rank-badge me-3">{index + 1}</div>
                                <div>
                                    <h5 className="mb-1 podcast-title">{result.metadata?.show}</h5>
                                    <p className="mb-1 episode-info">
                                        <strong>Episode:</strong> {result.metadata?.title}
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
                                <h5 className="card-title podcast-title">{selectedShow.metadata?.show}</h5>
                                <p className="card-text main-text">{selectedShow.metadata?.description}</p>
                                <p className="card-text episode-info">
                                    <strong>Episode:</strong> {selectedShow.metadata?.title}
                                </p>
                                <p className="card-text episode-info">
                                    <strong>Languages:</strong> {selectedShow.metadata?.language}
                                </p>
                                <p className="card-text episode-info">
                                    <strong>Author:</strong> {selectedShow.metadata?.publisher}
                                </p>
                                <p className="card-text episode-info">
                                    <strong>RSS Link:</strong> <a href={selectedShow.metadata?.rss_link} target="_blank" rel="noopener noreferrer">{selectedShow.metadata?.rss_link}</a>
                                </p>
                                <p className="card-text episode-info">
                                    <strong>Chunk: </strong>
                                    <span
                                        dangerouslySetInnerHTML={{ __html: selectedShow.transcript.chunk }}
                                    ></span>
                                </p>
                                <p className="card-text episode-info">
                                    {Math.round(parseFloat(selectedShow.transcript.start_time))}s → 
                                    {Math.round(parseFloat(selectedShow.transcript.end_time))}s
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
        )}
        </div>
    );
};

export default Search;