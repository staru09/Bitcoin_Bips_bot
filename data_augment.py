import openai
import csv
import os
import sys
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

csv.field_size_limit(10**9)

API_BASE_URL = "https://qwen7b.gaia.domains/v1"
MODEL_NAME = "qwen7b"
API_KEY = "gaia-"

class ProcessingError(Exception):
    """Custom exception for processing failures after retries"""
    pass

def create_retry_decorator():
    def after_retry(retry_state):
        if retry_state.attempt_number >= 2: 
            raise ProcessingError("Failed to process after maximum retries")
        print(f"Retry attempt {retry_state.attempt_number} after {retry_state.outcome.exception()}")

    return retry(
        retry=retry_if_exception_type((openai.APIError, openai.APITimeoutError)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=after_retry
    )

@create_retry_decorator()
def make_api_call(client, messages, model):
    return client.chat.completions.create(
        messages=messages,
        model=model,
        stream=False,
    )

def summarize(source_text):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    messages = [
        {
            "role": "system",
            "content": """
            You are an expert bitcoin developer whose working on the project to analyse all the BIPs. Your task is to:

            1. Summarize Code-related Files:
            - Focus on key changes in the code, including additions, deletions, and modifications.
            - Capture essential details such as the purpose of the code, any new functions, classes, or methods, and the overall impact of these changes on the project.
            - Highlight any dependencies, error handling, or performance implications.

            2. Summarize Markdown Files:
            - Extract key points from documentation, readme files, and other markdown content.
            - Identify sections related to project setup, usage instructions, change logs, or contributor guidelines.
            - Note updates in the documentation and the implications for users or developers.
            """,
        },
        {
            "role": "user",
            "content": source_text,
        }
    ]
    chat_completion = make_api_call(client, messages, MODEL_NAME)
    return chat_completion.choices[0].message.content

def qgen(source_text):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    messages = [
        {
            "role": "system",
            "content": "Respond with a list of 10 questions. The text in the user message must contain specific answers to each question. Each question must be on its own line. Just list the questions without any introductory text or numbers.",
        },
        {
            "role": "user",
            "content": source_text,
        }
    ]
    chat_completion = make_api_call(client, messages, MODEL_NAME)
    return chat_completion.choices[0].message.content

def agen(source_text, question):
    client = openai.OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    messages = [
        {
            "role": "system",
            "content": "Give a comprehensive and well-reasoned answer to the user question strictly based on the context below and try to give a detailed explanation while answering the questions. Also try to add some bonus tip to in each answer and some relevant example outside of the content.\n" + source_text
        },
        {
            "role": "user",
            "content": question,
        }
    ]
    chat_completion = make_api_call(client, messages, MODEL_NAME)
    return chat_completion.choices[0].message.content

def process_row(row, csv_writer, processed_contents, row_count):
    try:
        main_content = row[0]

        if main_content in processed_contents:
            print(f"Skipping row because content has already been processed")
            return row_count, 0

        if len(main_content) > 32000:
            print(f"Skipping row {row_count + 1}: content exceeds 32000 characters")
            return row_count, 0

        summary = summarize(main_content)
        qs = qgen(main_content)
        qna_list = []
        
        for q in qs.splitlines():
            if len(q.strip()) == 0:
                continue
            answer = agen(main_content, q)
            qna_list.append(f"Q: {q}\nA: {answer}")

        csv_writer.writerow([main_content, f"Summary:\n{summary}"])
        for qna in qna_list:
            csv_writer.writerow([main_content, qna])
        
        processed_contents.add(main_content)
        row_count += 1
        print(f"Processed row {row_count}")
        return row_count, 0

    except ProcessingError as pe:
        print(f"Skipping row {row_count + 1} due to timeout: {str(pe)}")
        return row_count, 1
    except Exception as e:
        print(f"Error processing row {row_count + 1}: {str(e)}")
        return row_count, 1


def load_processed_contents(output_path):
    processed = set()
    if os.path.exists(output_path):
        with open(output_path, 'r', newline='', encoding='utf-8') as outfile:
            csv_reader = csv.reader(outfile)
            for row in csv_reader:
                processed.add(row[0])
    return processed

def main():
    if len(sys.argv) != 3:
        logging.error("Usage: python summarizer.py <input_csv> <output_csv>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    processed_contents = load_processed_contents(output_path)
    row_count = 0
    skipped_rows = 0

    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
             open(output_path, 'a', newline='', encoding='utf-8') as outfile:
            
            csv_reader = csv.reader(infile)
            csv_writer = csv.writer(outfile)

            for row in csv_reader:
                row_count, skipped = process_row(row, csv_writer, processed_contents, row_count)
                skipped_rows += skipped

                outfile.flush()

    except KeyboardInterrupt:
        print("Process interrupted by user. Progress saved.")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        print(f"Modified data has been written to {output_path}")
        print(f"Total rows summarized: {row_count}")
        print(f"Total rows skipped: {skipped_rows}")

if __name__ == "__main__":
    main()
