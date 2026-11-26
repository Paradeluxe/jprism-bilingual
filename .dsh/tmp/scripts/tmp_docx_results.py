import docx, re
d = docx.Document(r"manuscript/JSpace_Liu_Nov18_2026.docx")
paras=[x.text.strip() for x in d.paragraphs]
idx=[i for i,t in enumerate(paras) if re.match(r"^3\.?\s*Results", t)]
print("Results idx:", idx)
if idx:
    s=idx[0]
    for i in range(s, min(s+12, len(paras))):
        print(f"--- [{i}] ---")
        print(paras[i][:1200])
