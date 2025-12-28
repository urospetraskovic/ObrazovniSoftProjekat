# Read the new function
with open('app_new_owl_function.py', 'r') as f:
    new_func = f.read()

# Read app.py
with open('app.py', 'r') as f:
    content = f.read()

# Find the start and end of the old function
start_idx = content.find('def generate_owl_from_relationships(lesson, relationships):')
end_idx = content.find('\ndef generate_turtle_from_relationships(', start_idx)

if start_idx != -1 and end_idx != -1:
    # Replace the function
    new_content = content[:start_idx] + new_func + '\n\n' + content[end_idx+1:]
    
    # Write back
    with open('app.py', 'w') as f:
        f.write(new_content)
    
    print("✓ Function replaced successfully!")
    print(f"  Old function: {end_idx - start_idx} chars")
    print(f"  New function: {len(new_func)} chars")
else:
    print("✗ Could not find function boundaries")
    print(f"  Start index: {start_idx}")
    print(f"  End index: {end_idx}")
