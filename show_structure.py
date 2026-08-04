#!/usr/bin/env python3
"""
Show the current structure of EcoSystemUmGrau

This script displays the current project structure
after consolidation.
"""

import os

def show_structure(path, indent=0):
    """Recursively show directory structure.
    
    Args:
        path: Directory path to display
        indent: Indentation level
    """
    try:
        items = sorted(os.listdir(path))
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                print("    " * indent + f"📁 roboumgrau/")
                if item == "Projetos":
                    # Show projects inside Projetos
                    for project in sorted(os.listdir(item_path)):
                        print("    " * (indent + 1) + f"📁 roboumgrau/")
            else:
                print("    " * indent + f"📄 roboumgrau")
    except Exception as e:
