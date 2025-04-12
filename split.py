def split_text_into_chunks(file_path, output_path, chunk_size=200):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    cleaned_text = ' '.join(text.split())

    words = cleaned_text.split()

    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    formatted_text = '\n\n'.join(chunks)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(formatted_text)

input_file = 'bips.txt'
output_file = 'split_bips.txt'
split_text_into_chunks(input_file, output_file)
