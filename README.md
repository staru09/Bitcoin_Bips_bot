# Bitcoin Improvement Protocol Bot

### github_parser.py
This script converts the content of a github repo into a text file. This can be used with a vector db to create a knowledge base.

### data_augment.py
This script augments the data scraped from the github repo and generate a CSV file with summary and QnA pairs for each file loaded from the github repo.

### split.py
This script converts the text file into chunks of 200 words.

### vector_db.sh
This script, based on WasmEdge, converts text files into a vector database. It can be used with a sample chatbot UI utilizing quantized open-source models.

### oss_bot.sh
This script, based on gaianet can be used to host a OSS model as chatbot with the custom knowledge base hosted on huggingface. 

References:-
1. https://github.com/GaiaNet-AI/gaianet-node
2. https://github.com/GaiaNet-AI/chatbot-ui
3. https://github.com/GaiaNet-AI/embedding-tools
4. https://github.com/GaiaNet-AI/node-configs 

