#!/usr/bin/env python3
# this_file: debug_content_search.py
#
# Simple debug test to understand why content search isn't finding matches

import tempfile
from pathlib import Path
import vexy_glob
import shutil

def debug_content_search():
    """Debug content search functionality with simple test case"""
    print("🐛 Debugging Content Search")
    print("=" * 30)
    
    # Create a simple test directory
    temp_dir = Path(tempfile.mkdtemp(prefix="debug_content_"))
    
    try:
        # Create a few test files with known content
        test_files = [
            ("test1.py", "# TODO: implement this function\nclass MyClass:\n    pass"),
            ("test2.js", "// TODO: add error handling\nclass APIController {\n    constructor() {}\n}"),
            ("test3.txt", "This file contains TODO items\nand class references")
        ]
        
        for filename, content in test_files:
            (temp_dir / filename).write_text(content)
            print(f"Created {filename} with content:")
            print(f"  {repr(content)}")
        
        print(f"\nTest directory: {temp_dir}")
        
        # Test 1: Simple literal search
        print("\n--- Test 1: Search for 'TODO' ---")
        results = list(vexy_glob.search("TODO", str(temp_dir)))
        print(f"Found {len(results)} matches")
        for result in results:
            print(f"  {result}")
        
        # Test 2: Simple word search
        print("\n--- Test 2: Search for 'class' ---")
        results = list(vexy_glob.search("class", str(temp_dir)))
        print(f"Found {len(results)} matches")
        for result in results:
            print(f"  {result}")
        
        # Test 3: Check file finding first
        print("\n--- Test 3: Basic file finding ---")
        files = list(vexy_glob.find("*", str(temp_dir)))
        print(f"Found {len(files)} files:")
        for file in files:
            print(f"  {file}")
        
        # Test 4: Manual verification
        print("\n--- Test 4: Manual verification ---")
        for filename, content in test_files:
            filepath = temp_dir / filename
            if "TODO" in content:
                print(f"✅ {filename} contains 'TODO'")
            if "class" in content:
                print(f"✅ {filename} contains 'class'")
                
        # Test 5: Try with different search parameters
        print("\n--- Test 5: Search with different parameters ---")
        try:
            results = list(vexy_glob.search("TODO", str(temp_dir), hidden=True, no_ignore=True))
            print(f"Search with expanded options: {len(results)} matches")
        except Exception as e:
            print(f"Error with expanded search: {e}")
    
    finally:
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up {temp_dir}")

def test_vexy_glob_api():
    """Test the basic vexy_glob API to ensure it's working"""
    print("\n🔧 Testing vexy_glob API")
    print("=" * 25)
    
    temp_dir = Path(tempfile.mkdtemp(prefix="api_test_"))
    
    try:
        # Create test file
        (temp_dir / "test.py").write_text("print('hello world')")
        
        # Test find function
        print("Testing find() function:")
        files = list(vexy_glob.find("*.py", str(temp_dir)))
        print(f"  Found {len(files)} .py files")
        
        # Test search function signature
        print("\nTesting search() function signature:")
        import inspect
        sig = inspect.signature(vexy_glob.search)
        print(f"  search{sig}")
        
        # Test with minimal search
        print("\nTesting minimal search:")
        results = list(vexy_glob.search("hello", str(temp_dir)))
        print(f"  Found {len(results)} matches for 'hello'")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    debug_content_search()
    test_vexy_glob_api()
    print("\n✅ Debug complete!")