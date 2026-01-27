from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import threading

# Use FLAN-T5 Base for faster performance (approx 1GB download)
MODEL_NAME = "google/flan-t5-base"
tokenizer = None
model = None
model_lock = threading.Lock()

def init_t5():
    global tokenizer, model
    with model_lock:
        if model is None:
            print(f"Loading {MODEL_NAME} model...")
            tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
            # Force CPU for reliability if multiple models are loaded
            device = "cpu" 
            model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)
            print(f"{MODEL_NAME} model loaded on {device}.")

def summarize_with_t5(text, min_words=300, max_words=500, custom_prompt=None):
    try:
        if model is None:
            init_t5()

        device = "cpu"

        # Updated Prompt for cleaner structure
        if custom_prompt:
            input_text = custom_prompt.format(text=text)
        else:
            input_text = (
                "Summarize the following financial news article in a clear, professional manner. "
                "Highlight key points using bullet points if possible. "
                "Ensure the text is grammatically correct and free of typos:\n\n"
                f"{text}"
            )

        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(device)

        # Convert word counts to approximate token counts (1 word ~= 1.3 tokens)
        min_tokens = int(min_words * 1.3)
        max_tokens = int(max_words * 1.3)
        
        # Safety: If input is too short, don't force a long summary which causes hallucination
        input_length = inputs.input_ids.shape[1]
        if input_length < min_tokens:
            print(f"Warning: Input text is short ({input_length} tokens). Adjusting min_new_tokens to avoid hallucination.")
            min_tokens = min(50, input_length) # At least produce something, but don't force 400
            max_tokens = min(max_tokens, int(input_length * 1.5) + 100)

        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=max_tokens,
                min_new_tokens=min_tokens,
                num_beams=4,                 # Increased to 4 for higher quality (reduces typos)
                repetition_penalty=1.2,
                length_penalty=1.0,
                early_stopping=True
            )
        
        raw_summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return format_summary(raw_summary)

    except Exception as e:
        print(f"T5 Summarization Error: {e}")
        return f"Error generating summary with T5: {str(e)}"

def format_summary(text):
    """
    Post-processes the T5 output to improve readability and fix specific artifacts.
    """
    if not text:
        return ""
    
    import re
    
    # 1. Fix "AcronymWord" joining (e.g., "NTPCis" -> "NTPC is")
    # Matches a sequence of Caps followed immediately by lowercase
    text = re.sub(r'([A-Z]{2,})([a-z])', r'\1 \2', text)
    
    # NEW: Fix "lowercaseUppercase" (e.g. "lastQ3" -> "last Q3")
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # NEW: Fix "digitWord" or "wordDigit" (e.g. "Fy26" -> "Fy 26")
    text = re.sub(r'([a-z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([A-Z])', r'\1 \2', text)

    # 2. Fix "wordS" casing at end of word (e.g., "expectS" -> "expects")
    # Matches lowercase char followed by 'S' followed by space or punctuation
    text = re.sub(r'([a-z])S(\b|[^a-zA-Z])', r'\1s\2', text)

    # 3. Fix common period spacing (e.g. "end.Start" -> "end. Start")
    text = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', text)

    # 4. Known Model Corrections (Specific to Indian Finance context)
    text = text.replace("Koatak", "Kotak")
    text = text.replace("Institutionali", "Institutional")
    text = text.replace("Motilal Oowal", "Motilal Oswal")
    text = text.replace("O'Swal", "Oswal")

    # 5. Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    # 6. Remove hallucinated footer phrases (Aggressive)
    stop_phrases = [
        "Read More", "Click here", "Create your own portfolio", "All rights reserved", 
        "Disclaimer", "Download", "Follow us", "copyright", 
        "This article was originally published", "prior written consent", 
        "Bloomberg Business", "Please try again later"
    ]
    
    for phrase in stop_phrases:
        if phrase.lower() in text.lower():
            idx = text.lower().find(phrase.lower())
            if idx > 0:
                text = text[:idx].strip()
                
    # 7. Truncate at pipe symbol | which often starts a footer
    if "|" in text:
        text = text.split("|")[0].strip()
    
    # 8. Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)

    # 9. Ensure proper ending
    # If the text was cut off, it might end weirdly. Ensure it ends with a period.
    if text and text[-1] not in ['.', '!', '?']:
        text += '.'

    return text



if __name__ == "__main__":
    test_text = "The Federal Reserve kept interest rates steady on Wednesday but took a major step toward lowering them in the coming months in a policy statement that gave a nod to inflation's decline. The central bank's latest move leaves its benchmark rate in a range between 5.25% and 5.5%, where it has been since July."
    print("Testing T5 Summarization...")
    print(summarize_with_t5(test_text))
