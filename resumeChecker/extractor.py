import pdfplumber as pfp
f=pfp.open("Users/yuvraj/Desktop/SkillMap/resumeChecker/test_resume.pdf")
for i in f.pages:
    print(i.extract_text)