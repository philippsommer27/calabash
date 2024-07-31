from typing import Dict, List

def build_process_tree(filename: str) -> Dict[str, List[str]]:
    process_tree: Dict[str, List[str]] = {}
    
    try:
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split(' -> ')
                if len(parts) == 2:
                    parent_part, child_part = parts
                    parent_pid = parent_part[parent_part.index('(')+1:parent_part.index(')')]
                    child_pid = child_part[child_part.index('(')+1:child_part.index(')')]
                    
                    if parent_pid not in process_tree:
                        process_tree[parent_pid] = []
                    process_tree[parent_pid].append(child_pid)
    except FileNotFoundError:
        raise Exception(f"File not found: {filename}")
    except Exception as e:
        raise Exception(f"Error processing file {filename}: {e}")
    
    return process_tree

def find_all_descendants(process_tree: Dict[str, List[str]], pid: str) -> List[str]:
    descendants: List[str] = []
    stack: List[str] = [pid]
    
    while stack:
        current_pid = stack.pop()
        descendants.append(current_pid)
        
        if current_pid in process_tree:
            stack.extend(process_tree[current_pid])
    
    return descendants

def resolve(filename: str, target_pid: str) -> List[int]:
    process_tree = build_process_tree(filename)
    descendants = find_all_descendants(process_tree, target_pid)
    return list(map(int, descendants))
