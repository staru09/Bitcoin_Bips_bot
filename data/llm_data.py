import csv
import json
import re
import pandas as pd

def process_csv_to_alpaca(input_csv, output_json):
    alpaca_data = []
    
    df = pd.read_csv(input_csv, header=None)
    
    full_text = "\n".join(df[1].astype(str).tolist())
    
    entries = re.split(r'(?=Q: |Summary:)', full_text)
    
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
            
        if entry.startswith("Q: "):
            qa_match = re.match(r'Q: (.*?)(?:\n|\r\n)A: (.*)', entry, re.DOTALL)
            if qa_match:
                question = qa_match.group(1).strip()
                answer = qa_match.group(2).strip()
                
                alpaca_entry = {
                    "instruction": f"Answer the following question about Bitcoin Improvement Proposal.:",
                    "input": question,
                    "output": answer,
                    "system": "You are a helpful assistant that provides accurate information about Bitcoin Improvement Proposal.",
                    "history": []
                }
                alpaca_data.append(alpaca_entry)
                
        elif entry.startswith("Summary:"):
            summary_content = entry.replace("Summary:", "").strip()
            
            doc_name_match = re.search(r'Summary of `(.*?)`', summary_content)
            doc_name = doc_name_match.group(1) if doc_name_match else "a document"
            
            alpaca_entry = {
                "instruction": f"Provide a summary of {doc_name}",
                "input": "",
                "output": summary_content,
                "system": "You are a helpful assistant that summarizes technical cryptocurrency documents accurately and concisely.",
                "history": []
            }
            alpaca_data.append(alpaca_entry)
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(alpaca_data, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {len(alpaca_data)} entries and saved to {output_json}")
    return alpaca_data

if __name__ == "__main__":
    input_file = r"C:\Users\91745\OneDrive\Desktop\Summer Of Bitcoin\Bitcoin_Bips_bot\data\bips_augmented.csv"
    output_file = r"C:\Users\91745\OneDrive\Desktop\Summer Of Bitcoin\Bitcoin_Bips_bot\data\data.json"
    
    processed_data = process_csv_to_alpaca(input_file, output_file)
    print(f"First entry sample: {json.dumps(processed_data[0], indent=2)}")
