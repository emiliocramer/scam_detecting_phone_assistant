from transformers import GPT2TokenizerFast


def truncate_text(text, token_limit):
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    tokens = tokenizer.encode(text, truncation=True, max_length=token_limit)
    truncated_text = tokenizer.decode(tokens, skip_special_tokens=True)

    return truncated_text
