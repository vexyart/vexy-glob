#!/usr/bin/env python3
# this_file: debug_rust_direct.py
#
# Test calling the Rust functions directly to isolate the issue

import tempfile
from pathlib import Path
import shutil

def test_rust_functions():
    """Test calling Rust functions directly"""
    print("🔧 Testing Rust Functions Directly")
    print("=" * 35)
    
    # Import the Rust module directly
    try:
        from vexy_glob import _vexy_glob
        print("✅ Successfully imported _vexy_glob")
    except ImportError as e:
        print(f"❌ Failed to import _vexy_glob: {e}")
        return
    
    # Create test directory
    temp_dir = Path(tempfile.mkdtemp(prefix="rust_test_"))
    
    try:
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("# TODO: implement this\nclass MyClass:\n    pass")
        
        print(f"Created test file: {test_file}")
        print(f"Content: {test_file.read_text()!r}")
        
        # Test 1: Direct Rust find() call
        print("\n--- Test 1: Direct Rust find() call ---")
        try:
            results = list(_vexy_glob.find(
                paths=[str(temp_dir)],
                glob="*.py",
                as_path_objects=False,
                yield_results=True,
                threads=0
            ))
            print(f"find() results: {len(results)} files")
            for result in results:
                print(f"  {result}")
        except Exception as e:
            print(f"find() error: {e}")
        
        # Test 2: Direct Rust search() call
        print("\n--- Test 2: Direct Rust search() call ---")
        try:
            results = list(_vexy_glob.search(
                content_regex="TODO",
                paths=[str(temp_dir)],
                glob="*",
                as_path_objects=False,
                yield_results=True,
                threads=0
            ))
            print(f"search() results: {len(results)} matches")
            for result in results:
                print(f"  {result}")
        except Exception as e:
            print(f"search() error: {e}")
            
        # Test 3: Try different search patterns
        print("\n--- Test 3: Different search patterns ---")
        for pattern in ["TODO", "class", "implement"]:
            try:
                results = list(_vexy_glob.search(
                    content_regex=pattern,
                    paths=[str(temp_dir)],
                    glob="*",
                    as_path_objects=False,
                    yield_results=True,
                    threads=0,
                    _case_sensitive_content=False
                ))
                print(f"Pattern '{pattern}': {len(results)} matches")
            except Exception as e:
                print(f"Pattern '{pattern}' error: {e}")
                
        # Test 4: Inspect function signatures
        print("\n--- Test 4: Function signatures ---")
        try:
            import inspect
            print(f"find signature: {inspect.signature(_vexy_glob.find)}")
            print(f"search signature: {inspect.signature(_vexy_glob.search)}")
        except Exception as e:
            print(f"Signature inspection error: {e}")
    
    finally:
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up {temp_dir}")

if __name__ == "__main__":
    test_rust_functions()
    print("\n✅ Direct Rust testing complete!")