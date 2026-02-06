# Python script to format conversations
import re


def clean_ollama_chat(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # Split by speaker
    parts = re.split(r'(User:|Assistant:)', content)

    # Group into Q&A pairs
    conversations = []
    for i in range(1, len(parts) - 1, 2):
        if parts[i] == 'User:':
            question = parts[i + 1].strip()
            answer = parts[i + 3].strip() if i + 3 < len(parts) and parts[i + 2] == 'Assistant:' else ""
            if question and answer:
                conversations.append({
                    'question': question,
                    'answer': answer,
                    'type': 'qna'
                })

    # Save as JSON for easy import
    import json
    with open(output_file, 'w') as f:
        json.dump(conversations, f, indent=2)


# Usage
clean_ollama_chat('raw_export.txt', 'clean_conversations.json')
