import React, { useState, useRef, useEffect } from "react";
import 'bootstrap/dist/css/bootstrap.min.css';
import "./search.css";
import { API_BASE_URL, SEARCH_FILTERS, SEARCH_TYPES, RANKING_TYPES } from "./config";
import defaultPodcastImage from "./default_podcast.png";


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
];

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
    const [uniqueQueryTypes, setUniqueQueryTypes] = useState([]);


    useEffect(() => {
        setIsAudioVisible(false);
        if (audioRef.current && selectedShow?.metadata?.audio) {
            const startTime = parseFloat(selectedShow.transcript.start_time);
            if (!isNaN(startTime)) {
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


    const handleCheckboxChange = (episode) => {
        setCheckedEpisodes((prev) => {
            const isChecked = prev.some((ep) => ep.metadata?.episode_id === episode.metadata?.episode_id);
            return isChecked
                ? prev.filter((ep) => ep.metadata?.episode_id !== episode.metadata?.episode_id)
                : [...prev, episode];
        });
    };
    

    const handleSearch = async () => {
        setIsLoading(true);
        setSelectedShow(null);
        const params = {
            q: query,
            filter: selectedTag,
            type: searchType,
            ranking: searchType === "Ranking" ? rankingType : undefined,
            time: timeRange.value,
            selectedEpisodes: checkedEpisodes,
        };

        console.log("Search Parameters:", params);
        
        try {
            const response = await fetch(`${API_BASE_URL}/search?`, {
                method:"POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(params),
            });
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

            // Extract and save unique query types
            const queries = resultsWithIds
                .map((result) => result.transcript?.query)
                .filter((query) => query !== undefined && query !== null);
            const uniqueQueries = [...new Set(queries)];
            console.log("Unique Query Types:", uniqueQueries);
            setUniqueQueryTypes(uniqueQueries); // Save to state
            console.log("Unique Query Types:", uniqueQueryTypes);
        } catch (error) {
            console.error("Error fetching search results:", error);
            setResults([]);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div className="container-fluid podcast-container px-4 py-5">
            <h1 className="text-center mb-4">Advanced Podcast Search</h1>

            <div className="d-flex gap-2 mb-2">
                {FILTER_MAPPING.map((filter) => (
                    <button
                        key={filter.value}
                        className={`btn ${selectedTag === filter.value ? "btn-primary" : "btn-outline-primary"} text-small`}
                        onClick={() => setSelectedTag(filter.value)}
                    >
                        {filter.label}
                    </button>
                ))}
            </div>

            <div className="search-bar-container mb-4">
                <div className="input-group">
                    <input
                        type="text"
                        className="form-control search-input"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for podcasts..."
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                handleSearch();
                            }
                        }}
                    />
                    <button className="btn btn-primary search-button" onClick={handleSearch}>
                        <i className="bi bi-search"></i>
                    </button>
                </div>
            </div>

            {/* Advanced Search Accordion */}
            <div className="accordion-container mb-4">
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
                                                            className={`badge ${timeRange.value === interval.value ? 'bg-primary' : 'bg-secondary'}`}
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
           
            {isLoading ? (
                <div className="text-center my-5">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-3">Searching for podcasts...</p>
                </div>
            ) : (
                <div className="row">
                    {results.length > 0 ? (
                        <>
                            <div className="d-flex flex-row justify-content-between border-bottom mb-4">
                                <h2 className="results-heading">Search Results</h2>
                                {uniqueQueryTypes.length > 0 && (
                                    <p className="text-muted">
                                        Showing results for: {uniqueQueryTypes.join(", ")}
                                    </p>
                                )}
                            </div>

                            
                            <div className="row-12 mb-4 d-flex gap-3">
                                {/* Grid View of Results (Spotify-like) */}
                                <div className="col-md-4 mb-4">
                                    <div className="row row-cols-1 row-cols-md-2 row-cols-lg-2 row-cols-xl-3 g-4">
                                        {results.map((result, index) => (
                                            <div key={index} className="col">
                                                <div 
                                                    className={`podcast-card ${selectedShow === result ? "selected" : ""}`}
                                                    onClick={() => setSelectedShow(result)}
                                                >
                                                    <div className="podcast-card-inner">
                                                        <div className="position-relative">
                                                            <div className="rank-badge">{index + 1}</div>
                                                            <div className="podcast-image-container">
                                                                <img
                                                                    src={result.metadata.episode_image || defaultPodcastImage}
                                                                    alt={result.metadata?.title || "Podcast thumbnail"}
                                                                    className="podcast-image"
                                                                />
                                                                <div className="podcast-play-overlay">
                                                                    <button className="play-button">
                                                                        <i className="bi bi-play-circle-fill"></i>
                                                                    </button>
                                                                </div>
                                                            </div>
                                                            <div className="checkbox-container">
                                                                <input
                                                                    type="checkbox"
                                                                    className="form-check-input"
                                                                    checked={checkedEpisodes.some((ep) => ep.metadata?.episode_id === result.metadata?.episode_id)}
                                                                    onChange={(e) => {
                                                                        e.stopPropagation();
                                                                        handleCheckboxChange(result);
                                                                    }}
                                                                />
                                                            </div>
                                                        </div>
                                                        <div className="podcast-info">
                                                            <h5 className="podcast-title text-truncate">{result.metadata?.show}</h5>
                                                            <p className="podcast-episode text-truncate">{result.metadata?.title}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Selected Podcast Details */}
                                {selectedShow && (
                                    <div className="col-md-8">
                                        <div className="card border-0 shadow-sm">
                                            <div className="card-header bg-primary text-white py-3 d-flex justify-content-between align-items-center">
                                                <h5 className="mb-0 text-white">
                                                    <i className="bi bi-music-note-beamed me-2"></i>
                                                    {selectedShow.metadata.title}
                                                </h5>
                                            </div>
                                            <div className="card-body">      
                                                <div className="row mb-4">
                                                    <div className="col-md-3">
                                                        <img 
                                                            src={selectedShow.metadata.episode_image || defaultPodcastImage} 
                                                            alt={selectedShow.metadata?.title} 
                                                            className="img-fluid rounded"
                                                        />
                                                    </div>
                                                    <div className="col-md-9">
                                                        <div className="description-container">
                                                            {parseDescription(selectedShow.metadata?.description)}
                                                        </div>
                                                    </div>
                                                </div>
                                                                            
                                                <div className="row mb-4">
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

                                                    {selectedShow.metadata?.audio ? (
                                                            
                                                        <div className="col-md-4">
                                                            <div className="card bg-light">
                                                                <div className="card-header">
                                                                    <h6 className="mb-0">Play</h6>
                                                                </div>
                                                                <ul className="list-group list-group-flush">
                                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-2"
                                                                        onClick={() => handlePlayAudio(0)}
                                                                        style={{ cursor: "pointer" }}
                                                                    >
                                                                        <span className="fw-bold">
                                                                            <i className="bi bi-play-fill"></i>
                                                                        </span>
                                                                        <span className="text-muted">From beginning</span>
                                                                  </li>
                                                                    <li className="list-group-item d-flex justify-content-start align-items-center gap-2"
                                                                        onClick={() => handlePlayAudio(parseFloat(selectedShow.transcript.start_time))}
                                                                        style={{ cursor: "pointer" }}
                                                                    >
                                                                        <span className="fw-bold">
                                                                            <i className="bi bi-fast-forward-fill"></i>
                                                                        </span>
                                                                        <span className="text-muted">From transcript</span>
                                                                    </li>
                                                                </ul>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="col-md-4">
                                                            <div className="card bg-light">
                                                                <div className="card-header">
                                                                    <h6 className="mb-0">No Audio Available</h6>
                                                                </div>
                                                                <div className="card-body">
                                                                    <p className="text-muted mb-0">Audio is not available for this episode at the moment.</p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                   
                                                </div>

                                                {isAudioVisible && selectedShow.metadata.audio && (
                                                    <div className="row mb-4">
                                                        <div className="col-12">
                                                            <div className="audio-player-container">
                                                                <audio
                                                                    ref={audioRef}
                                                                    controls
                                                                    className="w-100"
                                                                >
                                                                    <source src={selectedShow.metadata.audio} type="audio/mpeg" />
                                                                    Your browser does not support the audio element.
                                                                </audio>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {selectedShow.transcript.chunk && (
                                                    <div className="row">
                                                        <div className="col-md-12">
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
                                                                        <i className="bi bi-arrow-right mx-2"></i>
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
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                            </div>

                        </>
                    ) : (
                        <div className="col-12 text-center my-5">
                            <div className="empty-state">
                                <i className="bi bi-search display-1 text-muted"></i>
                                <h3 className="mt-3">Ready to discover podcasts?</h3>
                                <p className="text-muted">Search for your favorite topics, shows, or episodes.</p>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Search;