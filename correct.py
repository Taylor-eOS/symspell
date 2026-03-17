import os
import re
from symspellpy import SymSpell

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

def correct_text_preserve_punct(text, sym_spell, max_edit_distance=2, ignore_terms_with_digits=True):
    def is_word_token(token):
        if not token.strip():
            return False
        if ignore_terms_with_digits and any(c.isdigit() for c in token):
            return False
        return bool(re.match(r'^[\wäöüÄÖÜß]+$', token))
    def replace_word(match):
        word = match.group(0)
        if not is_word_token(word):
            return word
        suggestions = sym_spell.lookup_compound(
            word,
            max_edit_distance=max_edit_distance,
            transfer_casing=True,
            ignore_non_words=True
        )
        if suggestions and suggestions[0].distance <= max_edit_distance:
            return suggestions[0].term
        return word
    pattern = r"[\wäöüÄÖÜß]+"
    corrected = re.sub(pattern, replace_word, text)
    return corrected

def main():
    dict_file = select_dictionary()
    if not dict_file:
        return
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    term_index = 0
    count_index = 1
    if not sym_spell.load_dictionary(dict_file, term_index, count_index):
        print(f"Could not load dictionary: {dict_file}")
        return
    try:
        with open(input_file, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    corrected = correct_text_preserve_punct(text, sym_spell)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(corrected)
        print("Corrected text written to file.")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()

