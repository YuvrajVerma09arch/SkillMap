import pdfplumber

try:
    def extract_data(fp):
     t = ""
     with pdfplumber.open(fp) as pdf:
        for i in pdf.pages:
            page_text = i.extract_text()
            if page_text:
                t += page_text

     if t=="":
        raise Exception("EMPTY OR SCANNED PDF")

     print(t)

except Exception as e:
    print("Error:", e)
