def detect_specialized_agent(
    goal: str
):

    goal_lower = goal.lower()

    if "stock" in goal_lower:

        return (
            "stock_agent",
            "stock_analysis"
        )

    if "crypto" in goal_lower:

        return (
            "crypto_agent",
            "crypto_analysis"
        )

    if "youtube" in goal_lower:

        return (
            "youtube_agent",
            "video_analysis"
        )

    if "linkedin" in goal_lower:

        return (
            "linkedin_agent",
            "linkedin_research"
        )

    if "marketing" in goal_lower:

        return (
            "marketing_agent",
            "digital_marketing"
        )

    if "startup" in goal_lower:

        return (
            "startup_agent",
            "startup_strategy"
        )

    return None