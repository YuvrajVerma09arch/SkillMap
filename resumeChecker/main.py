from extractor import extract_data
from cleaner import clean_data

raw_data=extract_data("resumeChecker/test_resume.pdf")
clean_data=clean_data(raw_data)