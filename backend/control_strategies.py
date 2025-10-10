def control_strategies(water_level, rainfall, location):
    """
    Returns control strategies based on water level and rainfall
    """
    suggestions = []

    # Pumping strategy
    if water_level > 1.5:
        suggestions.append(f"Activate pumps at {location}.")
    elif water_level > 0.9:
        suggestions.append(f"Prepare pumps at {location} for potential flooding.")
    
    # Diversion channels
    if water_level > 1.8:
        suggestions.append(f"Open diversion channels near {location}.")
    
    # Traffic rerouting
    if water_level > 1.2:
        suggestions.append(f"Reroute traffic away from {location} via safe routes.")
    
    return suggestions
