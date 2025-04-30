import React, { useState, useRef, useEffect } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import "./search.css";
import { API_BASE_URL, SEARCH_FILTERS, SEARCH_TYPES, RANKING_TYPES } from "./config";

const TIME_RANGE_INTERVALS = [
    { label: "30s", value: 30 },
    { label: "1m", value: 60 },
    { label: "2m", value: 120 },
    { label: "3m", value: 180 },
    { label: "5m", value: 300 },
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
    const [rankingType, setRankingType] = useState("BM-25");
    const [timeRange, setTimeRange] = useState(TIME_RANGE_INTERVALS[0]); 
    const [isAccordionOpen, setIsAccordionOpen] = useState(false);
    const [selectedTag, setSelectedTag] = useState(FILTER_MAPPING[0].value);
    const [isLoading, setIsLoading] = useState(false);
    const audioRef = useRef(null);
    const [isAudioVisible, setIsAudioVisible] = useState(false);
    

    useEffect(() => {
        setIsAudioVisible(false);
        if (audioRef.current && selectedShow?.metadata?.audio) {
            const startTime = parseFloat(selectedShow.transcript.start_time); // Convert to a number
            if (!isNaN(startTime)) { // Ensure the value is a valid number
                audioRef.current.currentTime = startTime;
            } else {
                console.warn("Invalid start_time value:", selectedShow.transcript.start_time);
            }
        }
    }, [selectedShow]);

    const handlePlayAudio = (startTime = 0) => {
        setIsAudioVisible(true);
        setTimeout(() => { // Wait for the audio player to render
            if (audioRef.current) {
                audioRef.current.pause(); // Pause the audio before setting the time
                audioRef.current.currentTime = startTime; // Set the start time
                audioRef.current.play(); // Play the audio after setting the time
            }
        }, 100); 
    };

    const parseDescription = (description) => {
        if (!description) return [];
    
        const parts = description.split(/---|This episode is sponsored by/i); // Split by known dividers
    
        return parts.map((part, index) => {
            const linkRegex = /(https?:\/\/[^\s]+)/g;
            const processedPart = part.split(linkRegex).map((chunk, idx) => {
                if (chunk.match(linkRegex)) {
                    return (
                        <a
                            key={idx}
                            href={chunk}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary"
                        >
                            {chunk}
                        </a>
                    );
                }
                return <span key={idx}>{chunk}</span>;
            });
    
            // Main description
            return (
                <div key={index} className="mb-3">
                    {processedPart}
                </div>
            );
        });
    };
    

    const handleSearch = async () => {
        setIsLoading(true);
        setSelectedShow(null);
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
            console.log(data);

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
            setIsLoading(false);
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

            

            {/* Advanced Search Accordion */}
            <div className="row justify-content-center mb-4">
                <div className="col-lg-12">
                    <div className="accordion shadow-sm" id="advancedSearchAccordion">
                        <div className="accordion-item border-0">
                            <h2 className="accordion-header" id="headingOne">
                                <button
                                    className={`accordion-button ${isAccordionOpen ? "" : "collapsed"} bg-light`}
                                    type="button"
                                    onClick={() => setIsAccordionOpen(!isAccordionOpen)}
                                    aria-expanded={isAccordionOpen}
                                    aria-controls="collapseOne"
                                >
                                    <i className="bi bi-sliders me-2"></i>
                                    Advanced Search Options
                                </button>
                            </h2>
                            <div
                                id="collapseOne"
                                className={`accordion-collapse collapse ${isAccordionOpen ? "show" : ""}`}
                                aria-labelledby="headingOne"
                                data-bs-parent="#advancedSearchAccordion"
                            >
                                <div className="accordion-body bg-light">
                                    <div className="row g-4">
                                        {/* Search Type */}
                                        <div className="col-md-4">
                                            <div className="card h-100 border-0 shadow-sm">
                                                <div className="card-body text-center">
                                                    <h5 className="card-title fw-bold text-primary mb-3">
                                                        <i className="bi bi-search me-2"></i>
                                                        Search Type
                                                    </h5>
                                                    <div className="btn-group w-100" role="group">
                                                        {SEARCH_TYPES.map((type) => (
                                                            <button
                                                                key={type}
                                                                className={`btn ${searchType === type ? "btn-primary" : "btn-outline-primary"}`}
                                                                onClick={() => setSearchType(type)}
                                                            >
                                                                {type}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        {/* Ranking Type */}
                                        <div className="col-md-4">
                                            <div className="card h-100 border-0 shadow-sm">
                                                <div className="card-body text-center">
                                                    <h5 className="card-title fw-bold text-primary mb-3">
                                                        <i className="bi bi-sort-numeric-down me-2"></i>
                                                        Ranking Type
                                                    </h5>
                                                    <div className="btn-group w-100" role="group">
                                                        {RANKING_TYPES.map((type) => (
                                                            <button
                                                                key={type}
                                                                className={`btn ${rankingType === type ? "btn-primary" : "btn-outline-primary"} ${searchType !== "Ranking" ? "opacity-50" : ""}`}
                                                                onClick={() => searchType === "Ranking" && setRankingType(type)}
                                                                disabled={searchType !== "Ranking"}
                                                            >
                                                                {type}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        {/* Time Range */}
                                        <div className="col-md-4">
                                            <div className="card h-100 border-0 shadow-sm">
                                                <div className="card-body text-center">
                                                    <h5 className="card-title fw-bold text-primary mb-3">
                                                        <i className="bi bi-clock-history me-2"></i>
                                                        Time Range
                                                    </h5>
                                                    <input
                                                        type="range"
                                                        className="form-range mb-2"
                                                        min={0}
                                                        max={TIME_RANGE_INTERVALS.length - 1}
                                                        step={1}
                                                        value={TIME_RANGE_INTERVALS.findIndex((interval) => interval.value === timeRange.value)}
                                                        onChange={(e) => setTimeRange(TIME_RANGE_INTERVALS[parseInt(e.target.value)])}
                                                    />
                                                    <div className="d-flex justify-content-between">
                                                        {TIME_RANGE_INTERVALS.map((interval, index) => (
                                                            <span 
                                                                key={index} 
                                                                className={`badge ${timeRange.value === interval.value ? 'bg-secondary' : 'bg-outline-primary'}`}
                                                            >
                                                                {interval.label}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
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
                                {result.metadata.episode_image ? (
                                    <div>
                                       <img
                                        src={result.metadata.episode_image}
                                        alt="Episode Thumbnail"
                                        className="img-thumbnail me-3"
                                        style={{ width: "100px", height: "100px", objectFit: "cover" }}
                                         />
                                    </div>
                                    ) : ""}
                                
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
                            <div className="card border-0 shadow-sm">
                                <div className="card-header bg-primary text-white py-3 d-flex justify-content-between align-items-center">
                                    <h5 className="mb-0 text-white">
                                        <i className="bi bi-music-note-beamed me-4"></i>
                                        {selectedShow.metadata.title}
                                    </h5>
                                </div>
                                <div className="card-body">      
                                    <div className="d-flex flox-row">
                                        {/* <p className="text-muted mb-4">{selectedShow.metadata?.description}</p> */}
                                        {parseDescription(selectedShow.metadata?.description)}
                                    </div>                              
                                    <div className="d-flex flex-row mb-3">

                                        <div className="col-md-8">
                                            <div className="card bg-light">
                                                <div className="card-header">
                                                    <h6 className="mb-0">
                                                        <i className="bi bi-info-circle me-2"></i>
                                                        Episode Info
                                                    </h6>
                                                </div>
                                                <ul className="list-group list-group-flush">
                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-3">
                                                        <span className="fw-bold">
                                                            <i className="bi bi-collection-play-fill"></i>
                                                        </span>
                                                        <span className="text-muted">{selectedShow.metadata?.show || "N/A"}</span>
                                                    </li>
                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-3">
                                                        <span className="fw-bold">
                                                            <i className="bi bi-person-bounding-box"></i>
                                                        </span>
                                                        <span className="text-muted">{selectedShow.metadata?.publisher || "N/A"}</span>
                                                    </li>
                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-3">
                                                        <span className="fw-bold">
                                                            <i className="bi bi-globe"></i>
                                                        </span>

                                                        <span className="text-muted">{selectedShow.metadata?.language || "N/A"}</span>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>

                                        <div className="col-md-4">
                                            <div className="card bg-light ms-4">
                                                <div className="card-header">
                                                    <h6> Play </h6>
                                                </div>
                                                <ul className="list-group list-group-flush">
                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-2"
                                                        onClick={() => handlePlayAudio(0)}
                                                        style={{ cursor: "pointer" }}
                                                    >
                                                        <span className="fw-bold">
                                                            <i className="bi bi-play-fill"></i>
                                                        </span>
                                                        <span className="text-muted">From beggining</span>
                                                    </li>
                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-2"
                                                        onClick={() => handlePlayAudio(parseFloat(selectedShow.transcript.start_time))}
                                                        style={{ cursor: "pointer" }}
                                                    >
                                                        <span className="fw-bold">
                                                            <i class="bi bi-fast-forward-fill"></i>
                                                        </span>
                                                        <span className="text-muted">From transcript</span>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="row m-2">
                                        <div className="col-12">
                                            {isAudioVisible && selectedShow.metadata.audio && (
                                                <div>
                                                    <audio
                                                        ref={audioRef}
                                                        controls
                                                        className="w-100"
                                                    >
                                                        <source src={selectedShow.metadata.audio} type="audio/mpeg" />
                                                        Your browser does not support the audio element.
                                                    </audio>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="row-md-12"></div>
                                        <div className="col-md-12">
                                            
                                            {selectedShow.transcript.chunk && (
                                                <div className="card bg-light mb-4">
                                                    <div className="d-flex justify-content-between align-items-center card-header">
                                                        <h6 className="mb-0">
                                                            <i className="bi bi-quote me-2"></i>
                                                            Relevant Transcript Found
                                                        </h6>
                                                        {selectedShow.transcript.start_time && selectedShow.transcript.end_time && (
                                                        <div className="d-flex justify-content-end align-items-center m-2">
                                                            <span className="badge bg-secondary">
                                                                {Math.round(parseFloat(selectedShow.transcript.start_time))}s
                                                            </span>
                                                            <i className="bi bi-arrow-right"></i>
                                                            <span className="badge bg-secondary">
                                                                {Math.round(parseFloat(selectedShow.transcript.end_time))}s
                                                            </span>
                                                        </div>
                                                    )}
                                                    </div>
                                                    <div className="card-body">
                                                        <p className="card-text" dangerouslySetInnerHTML={{ __html: selectedShow.transcript.chunk }}></p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                </div>
                            </div>
                    ) : (
                        results.length > 0 && (
                            <div className="card border-0 shadow-sm h-100">
                                <div className="card-body d-flex flex-column justify-content-center align-items-center p-5">
                                    <i className="bi bi-headphones" style={{ fontSize: "3rem" }}></i>
                                    <h5 className="mt-4 mb-2 text-center">Ready to explore podcasts</h5>
                                    <p className="text-muted text-center">Select an episode from the list to see details and listen</p>
                                </div>
                            </div>
                        )
                    )}
                </div>
            </div>
        )}
        </div>
    );
};

export default Search;