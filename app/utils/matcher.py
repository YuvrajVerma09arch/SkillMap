def calculate_match_score(seeker_skills, job_skills):
    """
    Calculates a match percentage between seeker's skills and job requirements.
    seeker_skills: List of strings (e.g., ['Python', 'Flask'])
    job_skills: List of strings (e.g., ['Python', 'AWS', 'Docker'])
    """
    if not job_skills:
        return 100 # If no skills required, everyone is a match!
    
    if not seeker_skills:
        return 0

    # Normalize to lowercase for better matching
    seeker_set = {s.lower().strip() for s in seeker_skills}
    job_set = {s.lower().strip() for s in job_skills}
    
    # Find matches
    matches = seeker_set.intersection(job_set)
    
    # Calculate Score
    score = (len(matches) / len(job_set)) * 100
    
    return round(score)