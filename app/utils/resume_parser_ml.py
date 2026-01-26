import os
import re
import pdfplumber
import language_tool_python
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1. PDF TEXT EXTRACTION
def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


# 2. GRAMMAR & SPELLING CHECKER
def check_grammar_quality(text):
    """
    Uses LanguageTool to check grammar mistakes.
    Returns grammar_score (0-100) and error count.
    NOW WITH RELAXED SCORING!
    """
    try:
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(text[:5000])
        
        # Filter out minor issues (only count real errors)
        serious_errors = [
            m for m in matches 
            if m.ruleIssueType in ['grammar', 'misspelling', 'typographical']
        ]
        
        word_count = len(text.split())
        if word_count == 0:
            return 85, 0  # Default to good score for empty
        
        
        error_count = len(serious_errors)
        
        if error_count == 0:
            grammar_score = 100
        elif error_count <= 5:
            grammar_score = 100 - (error_count * 2)  # -2 points per error
        elif error_count <= 15:
            grammar_score = 90 - ((error_count - 5) * 1.5)  # -1.5 points per error
        else:
            grammar_score = max(50, 75 - (error_count - 15))  # Minimum 50
        
        grammar_score = int(round(grammar_score))
        
        tool.close()
        return grammar_score, error_count
    
    except Exception as e:
        print(f"Grammar check error: {e}")
        return 85, 0  # Default to good score if check fails


# 3. KEYWORD EXTRACTION & MATCHING
def extract_keywords(text, top_n=20):
    """Extract important keywords using TF-IDF"""
    clean_text = re.sub(r'[^\w\s+#.-]', ' ', text.lower())
    
    try:
        vectorizer = TfidfVectorizer(
            max_features=top_n,
            stop_words='english',
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform([clean_text])
        feature_names = vectorizer.get_feature_names_out()
        
        scores = tfidf_matrix.toarray()[0]
        keywords = [(feature_names[i], scores[i]) for i in range(len(feature_names))]
        keywords.sort(key=lambda x: x[1], reverse=True)
        
        return [kw[0] for kw in keywords]
    except:
        return []


def calculate_keyword_match(resume_keywords, jd_keywords):
    """Calculate percentage of JD keywords found in resume"""
    if not jd_keywords:
        return 100, []
    
    jd_set = set(jd_keywords)
    resume_set = set(resume_keywords)
    
    matched = jd_set.intersection(resume_set)
    match_percentage = (len(matched) / len(jd_set)) * 100
    
    missing = list(jd_set - resume_set)
    
    return match_percentage, missing


# 4. SEMANTIC SIMILARITY (Deep Learning)
def calculate_semantic_similarity(resume_text, jd_text):
    """
    Uses Sentence Transformers to calculate deep semantic similarity.
    This captures meaning beyond just keywords.
    """
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        resume_embedding = model.encode(resume_text[:3000], convert_to_tensor=False)
        jd_embedding = model.encode(jd_text[:3000], convert_to_tensor=False)
        
        similarity = cosine_similarity(
            [resume_embedding], 
            [jd_embedding]
        )[0][0]
        
        return similarity * 100
    
    except Exception as e:
        print(f"Semantic similarity error: {e}")
        return 50


# 5. MAIN ANALYSIS FUNCTION (REBALANCED WEIGHTS)
def analyze_resume(resume_path, job_description):
    """
    Main ML-based resume analysis function.
    Returns same JSON format as the original Groq version.
    """
    
    # --- Step 1: Extract Text ---
    resume_text = extract_text_from_pdf(resume_path)
    
    if not resume_text or len(resume_text) < 50:
        return {
            "match_score": 0,
            "missing_required_skills": ["Error: PDF empty or unreadable"],
            "explanation": ["Could not extract text from resume."]
        }
    
    # --- Step 2: Grammar Check ---
    grammar_score, error_count = check_grammar_quality(resume_text)
    
    # --- Step 3: Keyword Analysis ---
    resume_keywords = extract_keywords(resume_text, top_n=30)
    jd_keywords = extract_keywords(job_description, top_n=25)
    
    keyword_match_score, missing_keywords = calculate_keyword_match(
        resume_keywords, 
        jd_keywords
    )
    
    # --- Step 4: Semantic Similarity ---
    semantic_score = calculate_semantic_similarity(resume_text, job_description)
    
    # --- Step 5: Calculate Final Score (REBALANCED) ---
    final_score = (
        semantic_score * 0.55 +      # 55% - Overall compatibility (increased)
        keyword_match_score * 0.35 +  # 35% - Keyword matching (increased)
        grammar_score * 0.10          # 10% - Grammar quality (REDUCED from 20%)
    )
    
    final_score = int(round(final_score))
    
    # --- Step 6: Generate Explanation ---
    explanation = []
    
    # Semantic analysis feedback
    if semantic_score >= 75:
        explanation.append(f"Strong semantic alignment ({semantic_score:.0f}/100): Resume content closely matches job requirements.")
    elif semantic_score >= 50:
        explanation.append(f"Moderate alignment ({semantic_score:.0f}/100): Resume has relevant experience but could be more targeted.")
    else:
        explanation.append(f"Weak alignment ({semantic_score:.0f}/100): Resume content doesn't strongly match the job description.")
    
    # Keyword matching feedback
    if keyword_match_score >= 70:
        explanation.append(f"Excellent keyword coverage ({keyword_match_score:.0f}%): Most required skills/terms are present.")
    elif keyword_match_score >= 40:
        explanation.append(f"Partial keyword match ({keyword_match_score:.0f}%): Some key terms are missing from resume.")
    else:
        explanation.append(f"Low keyword match ({keyword_match_score:.0f}%): Resume lacks many important job-specific terms.")
    
    # Grammar feedback (LESS HARSH)
    if grammar_score >= 90:
        explanation.append(f"Excellent writing quality ({grammar_score}/100): Professional presentation with minimal issues.")
    elif grammar_score >= 75:
        explanation.append(f"Good writing quality ({grammar_score}/100): Well-written with minor improvements possible.")
    elif grammar_score >= 60:
        explanation.append(f"Acceptable writing quality ({grammar_score}/100): Some grammar improvements recommended ({error_count} issues found).")
    else:
        explanation.append(f"Writing needs improvement ({grammar_score}/100): Multiple grammar errors detected ({error_count} issues).")
    
    # Overall verdict
    if final_score >= 75:
        explanation.append("Verdict: Strong candidate - Resume demonstrates clear fit for this role.")
    elif final_score >= 50:
        explanation.append("Verdict: Potential fit - Resume shows promise but needs targeted improvements.")
    else:
        explanation.append("Verdict: Weak match - Significant gaps between candidate profile and job requirements.")
    
    # --- Step 7: Format Missing Skills ---
    formatted_missing = missing_keywords[:5] if missing_keywords else []
    
    # --- Step 8: Return Results ---
    return {
        "match_score": final_score,
        "missing_required_skills": formatted_missing,
        "explanation": explanation
    }


# 6. QUICK TEST
if __name__ == "__main__":
    print("Resume analyzer ready! Import and use analyze_resume() function.")