# app/utils/matcher.py

def calculate_match_score(user_skills, job_skills):
    """
    Calculates similarity between user skills and job requirements.
    Uses Jaccard Similarity (Intersection over Union).
    """
    if not user_skills or not job_skills:
        return 0
    
    # Normalize: " Python " -> "python"
    u_set = set([s.strip().lower() for s in user_skills.split(',')])
    j_set = set([s.strip().lower() for s in job_skills.split(',')])
    
    # Find Intersection (Matching Skills)
    intersection = u_set.intersection(j_set)
    
    # Find Union (Total Unique Skills)
    union = u_set.union(j_set)
    
    if len(union) == 0:
        return 0
        
    # Score = (Matches / Total) * 100
    score = (len(intersection) / len(union)) * 100
    return round(score)

def get_recommended_jobs(user, all_jobs):
    """
    Takes a User object and a list of Job objects.
    Returns a list of tuples: [(Job, Score), (Job, Score)] sorted by high score.
    """
    # 1. Get User's Skills from their profile/resume (Assume we saved this string)
    # For now, let's pretend the user model has a 'skills' column
    user_skills = getattr(user, 'skills', "") 
    
    ranked_jobs = []
    
    for job in all_jobs:
        score = calculate_match_score(user_skills, job.required_skills)
        
        # Only show jobs with some relevance (e.g. > 10%)
        if score > 10:
            ranked_jobs.append((job, score))
    
    # Sort by Score (Descending)
    ranked_jobs.sort(key=lambda x: x[1], reverse=True)
    
    return ranked_jobs