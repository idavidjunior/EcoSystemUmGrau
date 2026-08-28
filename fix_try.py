with open('scripts/widget_grafo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the lines we need to fix
# The issue is around lines 766-798 (0-indexed: 765-797)
# We need to:
# 1. Add 'import platform' after 'import time'
# 2. Wrap the pids loop in a try-except and add platform check

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Add import platform after import time in instancia_unica
    if 'import time' in line and i > 0 and 'def instancia_unica' in ''.join(lines[max(0,i-5):i]):
        new_lines.append(line)
        new_lines.append('    import platform\n')
        i += 1
        continue
    
    # Find the line with 'if platform.system() != "Windows":'
    if 'if platform.system() != "Windows":' in line:
        # We need to wrap the pids loop in a try-except
        # The structure should be:
        # if platform.system() != "Windows":
        #     pids = psutil.pids()
        #     try:
        #         for pid in pids:
        #             ...
        #     except Exception as e:
        #         print(...)
        #         pass
        
        # Find the line with 'pids = psutil.pids()'
        # The current structure has:
        # if platform.system() != "Windows":
        #     pids = psutil.pids()
        #     for pid in pids:
        #         ...
        # except Exception as e:  <- this is wrong, no matching try
        
        # We need to insert 'try:' before 'for pid in pids:' and indent the loop body
        # and add the except block after the for loop
        
        # For now, let's just add the try: before 'for pid in pids:'
        # and fix the except block at the end
        pass
    
    new_lines.append(line)
    i += 1

# This is too complex. Let's write the whole fixed file directly.

print("Done analyzing")