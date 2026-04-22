def optimize_transitions(songs: List[Song]) -> List[Song]:
    # Use dynamic programming to minimize key distance and tempo change
    graph = build_compatibility_graph(songs)
    path = find_optimal_path(graph)
    return path
