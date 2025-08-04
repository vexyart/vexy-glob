#!/usr/bin/env python3
# this_file: debug_wrapper_call.py
#
# Debug the exact parameters being passed by the Python wrapper

import tempfile
from pathlib import Path
import shutil

def debug_wrapper_call():
    """Debug what the wrapper is actually calling"""
    print("🔍 Debugging Python Wrapper Call")
    print("=" * 35)
    
    # Create test directory
    temp_dir = Path(tempfile.mkdtemp(prefix="wrapper_debug_"))
    
    try:
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("# TODO: implement this\nclass MyClass:\n    pass")
        
        print(f"Test file: {test_file}")
        
        # Import modules
        from vexy_glob import _vexy_glob
        import vexy_glob
        
        # Monkey patch to intercept the call
        original_search = _vexy_glob.search
        
        def debug_search(*args, **kwargs):
            print("\n🔍 INTERCEPTED RUST CALL:")
            print(f"args: {args}")
            print(f"kwargs: {kwargs}")
            
            # Call original and capture result
            try:
                result = original_search(*args, **kwargs)
                print(f"✅ Rust call succeeded, returning: {type(result)}")
                return result
            except Exception as e:
                print(f"❌ Rust call failed: {e}")
                raise
        
        # Apply monkey patch
        _vexy_glob.search = debug_search
        
        # Test the failing wrapper call
        print("\n--- Testing wrapper call that fails ---")
        try:
            results = list(vexy_glob.search("TODO", "*", str(temp_dir)))
            print(f"Wrapper result: {len(results)} matches")
            for result in results:
                print(f"  {result}")
        except Exception as e:
            print(f"Wrapper failed: {e}")
        
        # Restore original function
        _vexy_glob.search = original_search
        
        # Test direct call for comparison
        print("\n--- Testing direct call that works ---")
        try:
            results = list(_vexy_glob.search(
                content_regex="TODO",
                paths=[str(temp_dir)],
                glob="*",
                as_path_objects=False,
                yield_results=True,
                threads=0
            ))
            print(f"Direct result: {len(results)} matches")
            for result in results:
                print(f"  {result}")
        except Exception as e:
            print(f"Direct call failed: {e}")
    
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    debug_wrapper_call()
    print("\n✅ Wrapper debugging complete!")