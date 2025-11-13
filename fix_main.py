# Read the corrupted file
with open('server/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where the duplication starts
lines = content.split('\n')

# Find the first occurrence of "from fastapi import"
first_import = None
second_import = None

for i, line in enumerate(lines):
    if 'from fastapi import FastAPI' in line:
        if first_import is None:
            first_import = i
        elif second_import is None:
            second_import = i
            break

print(f"First import at line: {first_import}")
print(f"Second import at line: {second_import}")

if second_import is not None:
    # Keep everything before the second import
    clean_content = '\n'.join(lines[:second_import])
    
    # Write the cleaned file
    with open('server/main.py', 'w', encoding='utf-8') as f:
        f.write(clean_content)
    print("File cleaned successfully!")
else:
    print("Could not find duplication, file might need manual review")
