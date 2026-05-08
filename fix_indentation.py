#!/usr/bin/env python3
"""Fix indentation errors caused by commented-out blocks"""
import re

with open('boteddver1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern: try/except/else/elif followed by only comments or whitespace
# We need to add 'pass' after any block that only has comments

lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    fixed_lines.append(line)
    
    # Check if this line starts a control block (try, except, else, elif, if, for, while, def, class, etc.)
    if re.match(r'^(\s*)(try|except|else|elif|if|for|while|def|class|with)[\s:{}]', line) and line.rstrip().endswith(':'):
        # Look ahead to see if next non-empty, non-comment line is at same/lower indentation
        current_indent = len(line) - len(line.lstrip())
        j = i + 1
        found_content = False
        
        while j < len(lines):
            next_line = lines[j]
            # Skip empty lines
            if not next_line.strip():
                j += 1
                continue
            # Skip comment-only lines
            if next_line.strip().startswith('#'):
                j += 1
                continue
            # Found a non-comment, non-empty line
            next_indent = len(next_line) - len(next_line.lstrip())
            
            # If indentation is not greater than current, we need 'pass'
            if next_indent <= current_indent:
                # Insert pass before this line
                pass_indent = ' ' * (current_indent + 4)
                fixed_lines.append(pass_indent + 'pass')
                found_content = True
            
            break
        
        if not found_content and j >= len(lines):
            # End of file - need pass
            pass_indent = ' ' * (current_indent + 4)
            fixed_lines.append(pass_indent + 'pass')
    
    i += 1

# Write back
with open('boteddver1.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed indentation issues")
