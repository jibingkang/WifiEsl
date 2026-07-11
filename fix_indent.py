with open('backend/api/tasks.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the try line (449) and finally line (695), indent everything between them
# Line numbers are 0-based in the list
try_line_idx = None
finally_line_idx = None
for i, line in enumerate(lines):
    if line.strip() == 'try:' and try_line_idx is None:
        # Make sure it's the one in execute_task_push (after push_lock.acquire)
        if i > 0 and 'push_lock.acquire()' in lines[i-1]:
            try_line_idx = i
    if line.strip() == 'finally:' and try_line_idx is not None and finally_line_idx is None:
        finally_line_idx = i
        break

if try_line_idx is None or finally_line_idx is None:
    print(f"Could not find try/finally: try={try_line_idx}, finally={finally_line_idx}")
    exit(1)

print(f"Found try at line {try_line_idx+1}, finally at line {finally_line_idx+1}")

# Indent all lines between try and finally (exclusive of try, exclusive of finally)
# The line after try should be indented, and all lines up to finally should be indented
for i in range(try_line_idx + 1, finally_line_idx):
    if lines[i].strip():  # non-empty line
        # Check if it's already indented more than try
        try_indent = len(lines[try_line_idx]) - len(lines[try_line_idx].lstrip())
        line_indent = len(lines[i]) - len(lines[i].lstrip())
        if line_indent <= try_indent:
            # Add 4 more spaces
            lines[i] = '    ' + lines[i]

with open('backend/api/tasks.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Indented try block content')
