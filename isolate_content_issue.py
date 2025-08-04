#!/usr/bin/env python3
# this_file: isolate_content_issue.py
#
# Isolate why content search works on small tests but fails on larger tests

import tempfile
from pathlib import Path
import shutil
import vexy_glob

def test_progressive_complexity():
    """Test with increasing complexity to find where it breaks"""
    print("🔍 Progressive Complexity Testing")
    print("=" * 35)
    
    base_dir = Path(tempfile.mkdtemp(prefix="progressive_test_"))
    
    try:
        # Test 1: Single file (like debug test)
        print("\n--- Test 1: Single file ---")
        (base_dir / "single.py").write_text("# TODO: implement this\nclass MyClass:\n    pass")
        
        results = list(vexy_glob.search("TODO", "*", str(base_dir)))
        print(f"Single file: {len(results)} matches")
        
        # Test 2: Multiple files, flat structure
        print("\n--- Test 2: Multiple files, flat ---")
        for i in range(5):
            (base_dir / f"multi_{i}.py").write_text(f"# TODO: implement function {i}\nclass Class{i}:\n    pass")
        
        results = list(vexy_glob.search("TODO", "*", str(base_dir)))
        print(f"Multiple flat files: {len(results)} matches")
        
        # Test 3: Files in subdirectories
        print("\n--- Test 3: Files in subdirectories ---")
        subdir = base_dir / "subdir"
        subdir.mkdir()
        for i in range(3):
            (subdir / f"nested_{i}.py").write_text(f"# TODO: nested function {i}\nclass NestedClass{i}:\n    pass")
        
        results = list(vexy_glob.search("TODO", "*", str(base_dir)))
        print(f"With subdirectories: {len(results)} matches")
        
        # Test 4: Different file extensions
        print("\n--- Test 4: Different file extensions ---")
        (base_dir / "test.js").write_text("// TODO: implement this\nclass JSClass {}")
        (base_dir / "test.txt").write_text("TODO: update this document\nclass references here")
        
        results = list(vexy_glob.search("TODO", "*", str(base_dir)))
        print(f"Mixed file types: {len(results)} matches")
        
        # Test 5: Test with explicit file pattern
        print("\n--- Test 5: Explicit file patterns ---")
        results_py = list(vexy_glob.search("TODO", "*.py", str(base_dir)))
        results_all = list(vexy_glob.search("TODO", "*", str(base_dir)))
        results_recursive = list(vexy_glob.search("TODO", "**/*", str(base_dir))) 
        
        print(f"*.py pattern: {len(results_py)} matches")
        print(f"* pattern: {len(results_all)} matches")
        print(f"**/* pattern: {len(results_recursive)} matches")
        
        # Test 6: Check what files are being found
        print("\n--- Test 6: File discovery analysis ---")
        all_files = list(vexy_glob.find("*", str(base_dir)))
        py_files = list(vexy_glob.find("*.py", str(base_dir)))
        recursive_files = list(vexy_glob.find("**/*", str(base_dir)))
        
        print(f"All files found (*): {len(all_files)}")
        print(f"Python files found (*.py): {len(py_files)}")  
        print(f"Recursive files found (**/*): {len(recursive_files)}")
        
        print("\nFile list:")
        for f in all_files:
            if Path(f).is_file():
                print(f"  FILE: {f}")
            else:
                print(f"  DIR:  {f}")
        
        # Test 7: Manual content verification
        print("\n--- Test 7: Manual content verification ---")
        for file_path in all_files:
            path = Path(file_path)
            if path.is_file() and path.suffix in ['.py', '.js', '.txt']:
                content = path.read_text()
                has_todo = "TODO" in content
                print(f"  {path.name}: {'✅' if has_todo else '❌'} contains TODO")
                if has_todo:
                    print(f"    Content preview: {content[:50]!r}...")
    
    finally:
        shutil.rmtree(base_dir)

def test_realistic_vs_simple():
    """Compare realistic file creation vs simple file creation"""
    print("\n\n🔬 Realistic vs Simple Content")
    print("=" * 32)
    
    # Test with simple content (like debug test)
    simple_dir = Path(tempfile.mkdtemp(prefix="simple_"))
    realistic_dir = Path(tempfile.mkdtemp(prefix="realistic_"))
    
    try:
        # Simple content
        (simple_dir / "simple.py").write_text("# TODO: implement this\nclass MyClass:\n    pass")
        
        # Realistic content (like the performance test)
        realistic_content = f"""# Python file
import os
import sys

class UserManager:
    def __init__(self):
        self.users = []
        
    def add_user(self, name):
        # TODO: validate user name
        self.users.append(name)
        
    class InnerClass:
        pass

def helper_function():
    # TODO: implement this
    return "helper"

class DatabaseManager(object):
    '''Database management class'''
    def __init__(self):
        super().__init__()
"""
        (realistic_dir / "realistic.py").write_text(realistic_content)
        
        # Test both
        simple_results = list(vexy_glob.search("TODO", "*", str(simple_dir)))
        realistic_results = list(vexy_glob.search("TODO", "*", str(realistic_dir)))
        
        print(f"Simple content: {len(simple_results)} matches")
        print(f"Realistic content: {len(realistic_results)} matches")
        
        # Show content preview
        print(f"\nSimple content preview:")
        print(f"  {(simple_dir / 'simple.py').read_text()!r}")
        
        print(f"\nRealistic content preview (first 200 chars):")
        print(f"  {realistic_content[:200]!r}...")
        
        # Test if it's a content length issue
        print(f"\nContent lengths:")
        print(f"  Simple: {len((simple_dir / 'simple.py').read_text())} bytes")
        print(f"  Realistic: {len(realistic_content)} bytes")
    
    finally:
        shutil.rmtree(simple_dir)
        shutil.rmtree(realistic_dir)

if __name__ == "__main__":
    test_progressive_complexity()
    test_realistic_vs_simple()
    print("\n✅ Isolation testing complete!")