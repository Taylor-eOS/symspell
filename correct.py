import os
import re
import pysbd
from symspellpy import SymSpell, Verbosity

output_file = "output.txt"
input_file = "input.txt"

def list_txt_files():
    exclude = {output_file, input_file, "requirements.txt"}
    files = [f for f in os.listdir('.') if f.lower().endswith('.txt') and f not in exclude]
    return sorted(files)

def select_dictionary():
    txt_files = list_txt_files()
    if not txt_files:
        print("No suitable .txt dictionary files found in current folder.")
        return None
    print("Available dictionary files:")
    for i, fname in enumerate(txt_files, 1):
        print(f"{i}. {fname}")
    try:
        choice = int(input("Enter number of dictionary to use: "))
        if 1 <= choice <= len(txt_files):
            return txt_files[choice - 1]
        else:
            print("Invalid number, using first file.")
            return txt_files[0]
    except ValueError:
        print("Not a number, using first file.")
        return txt_files[0]

def word_frequency(sym_spell, word):
    results = sym_spell.lookup(word.lower(), Verbosity.TOP, max_edit_distance=0)
    if results:
        return results[0].count
    return 0

def rejoin_split_words(tokens, sym_spell, min_join_freq_ratio=10):
    result = []
    i = 0
    while i < len(tokens):
        if i + 1 < len(tokens):
            joined = tokens[i] + tokens[i + 1]
            freq_joined = word_frequency(sym_spell, joined)
            freq_left = word_frequency(sym_spell, tokens[i])
            freq_right = word_frequency(sym_spell, tokens[i + 1])
            freq_parts_max = max(freq_left, freq_right, 1)
            if freq_joined > 0 and freq_joined >= freq_parts_max * min_join_freq_ratio:
                casing = tokens[i][0].isupper()
                merged = joined.capitalize() if casing else joined
                result.append(merged)
                i += 2
                continue
        result.append(tokens[i])
        i += 1
    return result

def correct_token(token, sym_spell, max_edit_distance):
    if not token or not token.strip():
        return token
    if any(c.isdigit() for c in token):
        return token
    if not re.match(r'^[^\W\d_]+$', token, re.UNICODE):
        return token
    results = sym_spell.lookup(token, Verbosity.TOP, max_edit_distance=max_edit_distance, transfer_casing=True)
    if results and results[0].distance <= max_edit_distance:
        return results[0].term
    return token

def split_into_sentences(text, lang="de"):
    segmenter = pysbd.Segmenter(language=lang, clean=False)
    paragraphs = text.split("\n")
    result = []
    for i, para in enumerate(paragraphs):
        if para.strip():
            result.extend(segmenter.segment(para))
        else:
            result.append(para)
        if i < len(paragraphs) - 1:
            result.append("\n")
    return result

def correct_sentence(sentence, sym_spell, max_edit_distance):
    if not sentence.strip():
        return sentence
    word_pattern = re.compile(r'([^\W\d_]+)', re.UNICODE)
    tokens = word_pattern.split(sentence)
    word_indices = [i for i, t in enumerate(tokens) if word_pattern.fullmatch(t)]
    words_only = [tokens[i] for i in word_indices]
    words_only = rejoin_split_words(words_only, sym_spell)
    joined_phrase = ' '.join(words_only)
    suggestions = sym_spell.lookup_compound(
        joined_phrase,
        max_edit_distance=max_edit_distance,
        transfer_casing=True,
        ignore_non_words=True
    )
    if suggestions:
        compound_words = suggestions[0].term.split()
    else:
        compound_words = words_only
    if len(compound_words) != len(words_only):
        compound_words = [correct_token(w, sym_spell, max_edit_distance) for w in words_only]
    result_tokens = list(tokens)
    for idx, wi in enumerate(word_indices):
        if idx < len(compound_words):
            result_tokens[wi] = compound_words[idx]
    return ''.join(result_tokens)

def correct_text(text, sym_spell, max_edit_distance=2, lang="de"):
    sentences = split_into_sentences(text, lang=lang)
    corrected = [correct_sentence(s, sym_spell, max_edit_distance) for s in sentences]
    return ''.join(corrected)

def main():
    dict_file = select_dictionary()
    if not dict_file:
        return
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    if not sym_spell.load_dictionary(dict_file, 0, 1):
        print(f"Could not load dictionary: {dict_file}")
        return
    try:
        with open(input_file, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    corrected = correct_text(text, sym_spell)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(corrected)
        print("Corrected text written to file.")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()

