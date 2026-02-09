import difflib

# 1. Define Common Skill Aliases (The "Thesaurus")
SKILL_ALIASES = {
    "js": "javascript",
    "reactjs": "react",
    "react.js": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "py": "python",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "aws": "amazon web services",
    "cpp": "c++",
    "c#": "csharp",
    "golang": "go"
}

def normalize_skill(skill):
    """
    Cleans a skill string: lowercase, stripped, and de-aliased.
    Input: "  ReactJS  " -> Output: "react"
    """
    if not skill:
        return ""
    clean = skill.strip().lower()
    return SKILL_ALIASES.get(clean, clean)

def calculate_match_score(user_skills, job_skills):
    """
    Calculates a smarter similarity score using Fuzzy Matching + Jaccard.
    """
    if not user_skills or not job_skills:
        return 0
    
    # 1. Normalize Inputs (Handle List or CSV String)
    if isinstance(user_skills, list):
        u_list = [normalize_skill(s) for s in user_skills]
    else:
        u_list = [normalize_skill(s) for s in user_skills.split(',')]

    if isinstance(job_skills, list):
        j_list = [normalize_skill(s) for s in job_skills]
    else:
        j_list = [normalize_skill(s) for s in job_skills.split(',')]
        
    # Convert to sets for uniqueness
    u_set = set([u for u in u_list if u])
    j_set = set([j for j in j_list if j])
    
    # 2. Find Matches (Direct + Fuzzy)
    matches = 0
    
    # Check every job requirement against user skills
    for job_skill in j_set:
        if job_skill in u_set:
            matches += 1
            continue
            
        # Fuzzy Check: If no exact match, check for "close enough"
        # e.g., "Github" vs "Git" -> might trigger if similarity > 0.8
        for user_skill in u_set:
            # difflib.SequenceMatcher gives a ratio 0.0 to 1.0
            similarity = difflib.SequenceMatcher(None, job_skill, user_skill).ratio()
            
            # If 80% similar, count as a match
            if similarity > 0.85: 
                matches += 1
                break
    
    # 3. Calculate Final Score (Intersection / Union)
    # Note: We use the count of matches we found manually
    total_unique_skills = len(u_set.union(j_set))
    
    if total_unique_skills == 0:
        return 0
        
    score = (matches / total_unique_skills) * 100
    
    # Bonus: Boost score slightly if they have ALL required skills
    # to differentiate 100% match from just "lots of skills"
    if matches == len(j_set):
        score = min(100, score * 1.2)
        
    return round(score)