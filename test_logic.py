from app.utils.resume_parser import analyze_resume

# 1. Create a fake dummy PDF for testing (or use a real one if you have it)
# For this test, we will mock the function to skip PDF reading if file doesn't exist, 
# BUT correct way is to put a real "sample.pdf" in your folder.
# Let's assume you have a 'sample_resume.pdf' in root. 
# If not, just run this to see if import works.

print("--- Testing Logic ---")

# Let's pretend we extracted this text (Simulating the PDF part)
fake_resume_text = "I am a Python Developer with experience in Flask and SQL."
fake_job_desc = "We need a Python Developer who knows Flask, SQL, Docker, and AWS."

# We will manually call the math part (Copying logic from parser for quick test)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

documents = [fake_resume_text, fake_job_desc]
vectorizer = TfidfVectorizer(stop_words='english')
matrix = vectorizer.fit_transform(documents)
score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]

print(f"Resume: {fake_resume_text}")
print(f"Job: {fake_job_desc}")
print(f"Match Score: {round(score * 100, 2)}%")
print("--- Test Complete ---")