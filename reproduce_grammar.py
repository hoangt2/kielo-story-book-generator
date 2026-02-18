from grammar_checker import check_grammar

bad_story = {
    "level": "Beginner",
    "pages": [
        {"page_number": 1, "text_fi": "Sari vastaa: 'Minulla on myös hyvä! Olen lomalla!'"}
    ]
}

print("Testing bad grammar...")
valid, feedback = check_grammar(bad_story)
print(f"Valid: {valid}")
print(f"Feedback: {feedback}")

if valid:
    print("FAILURE: Grammar checker incorrectly approved the bad sentence.")
else:
    print("SUCCESS: Grammar checker correctly caught the error.")
