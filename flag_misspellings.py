import os
import re
from symspellpy import SymSpell, Verbosity

input_file = "input.txt"
output_file = "flagged.txt"
max_edit_distance = 2
context_chars = 40

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

def load_symspell(dict_file):
    sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance, prefix_length=7)
    if not sym_spell.load_dictionary(dict_file, 0, 1):
        print(f"Could not load dictionary: {dict_file}")
        return None
    return sym_spell

def is_checkable_word(token):
    if not token or not token.strip():
        return False
    if any(c.isdigit() for c in token):
        return False
    if not re.match(r'^[^\W\d_]+$', token, re.UNICODE):
        return False
    return True

def is_known_word(word, sym_spell):
    results = sym_spell.lookup(word.lower(), Verbosity.TOP, max_edit_distance=0)
    return len(results) > 0

def find_misspellings(text, sym_spell):
    word_pattern = re.compile(r'[^\W\d_]+', re.UNICODE)
    flagged = []
    for match in word_pattern.finditer(text):
        token = match.group()
        if not is_checkable_word(token):
            continue
        if is_known_word(token, sym_spell):
            continue
        start = max(0, match.start() - context_chars)
        end = min(len(text), match.end() + context_chars)
        context = text[start:end].replace("\n", " ")
        suggestions = sym_spell.lookup(token.lower(), Verbosity.CLOSEST, max_edit_distance=max_edit_distance)
        suggestion_terms = [s.term for s in suggestions[:5]]
        flagged.append((token, match.start(), context, suggestion_terms))
    return flagged

def format_report(flagged):
    lines = []
    for token, pos, context, suggestions in flagged:
        suggestion_text = ", ".join(suggestions) if suggestions else "no suggestions"
        lines.append(f"[{pos}] \"{token}\" -> {suggestion_text}")
        lines.append(f"    context: ...{context}...")
    return "\n".join(lines)

def main():
    dict_file = select_dictionary()
    if not dict_file:
        return
    sym_spell = load_symspell(dict_file)
    if sym_spell is None:
        return
    try:
        with open(input_file, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    flagged = find_misspellings(text, sym_spell)
    report = format_report(flagged)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Found {len(flagged)} flagged words. Report written to {output_file}.")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()
