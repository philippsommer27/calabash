def build_process_tree(filename):
    process_tree = {}
    
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split(' -> ')
            if len(parts) == 2:
                parent_part, child_part = parts
                parent_pid = parent_part[parent_part.index('(')+1:parent_part.index(')')]
                child_pid = child_part[child_part.index('(')+1:child_part.index(')')]
                
                if parent_pid not in process_tree:
                    process_tree[parent_pid] = []
                process_tree[parent_pid].append(child_pid)
    
    return process_tree

def find_all_descendants(process_tree, pid):
    descendants = []
    stack = [pid]
    
    while stack:
        current_pid = stack.pop()
        descendants.append(current_pid)
        
        if current_pid in process_tree:
            stack.extend(process_tree[current_pid])
    
    return descendants

def resolve(filename, target_pid):
    process_tree = build_process_tree(filename)
    descendants = find_all_descendants(process_tree, target_pid)
    return descendants