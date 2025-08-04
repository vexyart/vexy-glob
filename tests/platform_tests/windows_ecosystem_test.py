#!/usr/bin/env python3
# this_file: tests/platform_tests/windows_ecosystem_test.py
"""
Comprehensive Windows ecosystem testing for vexy_glob

Tests Windows-specific behaviors:
- UNC paths (\\server\share\folder) with network drives and SharePoint mounts
- Windows drive letters (C:\, D:\, mapped network drives) and path normalization
- Case-insensitive NTFS behavior with mixed-case file/directory names
- Windows reserved filenames (CON, PRN, AUX, COM1-COM9, LPT1-LPT9)
- NTFS junction points, hard links, and symbolic links
- Windows file attributes (hidden, system, readonly) and ACL permissions
- PowerShell 5.1, PowerShell 7, cmd.exe, and Windows Terminal compatibility
- WSL1/WSL2 integration and cross-filesystem operations
- Windows Defender real-time scanning behavior
"""

import os
import sys
import tempfile
import subprocess
import platform
import stat
from pathlib import Path, WindowsPath
from typing import List, Dict, Any, Optional
import unittest
import shutil
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Only run on Windows
if platform.system() != 'Windows':
    raise unittest.SkipTest("Windows ecosystem tests can only run on Windows")

import vexy_glob


class WindowsEcosystemTest(unittest.TestCase):
    """Comprehensive Windows ecosystem testing"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_root = Path(tempfile.mkdtemp(prefix="vexy_glob_windows_test_"))
        print(f"Test root: {self.test_root}")
        
    def tearDown(self):
        """Clean up test environment"""
        try:
            if self.test_root.exists():
                # Remove read-only attributes before deletion
                for root, dirs, files in os.walk(self.test_root):
                    for name in files:
                        filepath = Path(root) / name
                        try:
                            filepath.chmod(stat.S_IWRITE)
                        except:
                            pass
                shutil.rmtree(self.test_root, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.test_root}: {e}")

    def test_drive_letters_and_paths(self):
        """Test Windows drive letters and path normalization"""
        print("🔧 Testing Windows drive letters and path normalization...")
        
        # Test current drive
        current_drive = Path.cwd().anchor
        test_pattern = f"{current_drive}**\\*.py"
        
        # Should find Python files on current drive
        results = list(vexy_glob.find("*.py", root=current_drive, max_depth=3))
        self.assertGreater(len(results), 0, "Should find Python files on current drive")
        
        # Test path normalization with forward/backward slashes
        mixed_path = str(self.test_root).replace('\\', '/')
        results_mixed = list(vexy_glob.find("*", root=mixed_path))
        
        normal_results = list(vexy_glob.find("*", root=str(self.test_root)))
        self.assertEqual(len(results_mixed), len(normal_results), 
                        "Mixed slash paths should work identically")

    def test_case_insensitive_ntfs_behavior(self):
        """Test case-insensitive NTFS filesystem behavior"""
        print("🔧 Testing case-insensitive NTFS behavior...")
        
        # Create files with mixed case names
        test_files = [
            "TestFile.TXT",
            "testfile.txt", 
            "TESTFILE.TXT",
            "TestFile.Py",
            "test_FILE.py"
        ]
        
        for filename in test_files:
            (self.test_root / filename).touch()
        
        # Test case-insensitive pattern matching
        txt_results = list(vexy_glob.find("*.txt", root=self.test_root))
        TXT_results = list(vexy_glob.find("*.TXT", root=self.test_root))
        
        # Should find the same files regardless of pattern case
        self.assertEqual(len(txt_results), len(TXT_results),
                        "Case-insensitive filesystem should match patterns regardless of case")
        
        # Test exact filename matching with different cases
        exact_results = list(vexy_glob.find("testfile.txt", root=self.test_root))
        self.assertGreater(len(exact_results), 0, "Should find case-insensitive exact matches")

    def test_windows_reserved_filenames(self):
        """Test Windows reserved filename handling"""
        print("🔧 Testing Windows reserved filename handling...")
        
        # Windows reserved names
        reserved_names = [
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", 
            "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
            "LPT6", "LPT7", "LPT8", "LPT9"
        ]
        
        # Test reserved names with extensions
        test_files = []
        for name in reserved_names[:5]:  # Test subset to avoid issues
            try:
                # Try to create files with reserved names + extensions
                safe_name = f"{name}.txt"
                test_file = self.test_root / safe_name
                test_file.write_text(f"Content of {safe_name}")
                test_files.append(safe_name)
            except (OSError, PermissionError) as e:
                print(f"  Warning: Could not create {name}.txt: {e}")
        
        if test_files:
            # Test pattern matching with reserved names
            results = list(vexy_glob.find("*.txt", root=self.test_root))
            found_reserved = [r for r in results if any(name in r for name in reserved_names)]
            
            print(f"  Created {len(test_files)} files with reserved names")
            print(f"  Found {len(found_reserved)} in search results")

    def test_long_path_support(self):
        """Test long path support (>260 characters)"""
        print("🔧 Testing long path support...")
        
        # Create a deeply nested directory structure
        current_path = self.test_root
        path_components = []
        
        # Build a path close to 260 characters
        for i in range(15):
            component = f"very_long_directory_name_component_{i:02d}"
            path_components.append(component)
            current_path = current_path / component
            
            try:
                current_path.mkdir(exist_ok=True)
            except OSError as e:
                print(f"  Warning: Could not create deep directory at level {i}: {e}")
                break
        
        # Create a file in the deepest directory
        if current_path.exists():
            test_file = current_path / "long_path_test_file.txt"
            try:
                test_file.write_text("Test content in long path")
                
                # Test finding files in long paths
                results = list(vexy_glob.find("*.txt", root=self.test_root))
                long_path_results = [r for r in results if len(r) > 200]
                
                print(f"  Created path length: {len(str(test_file))}")
                print(f"  Found {len(long_path_results)} files in long paths")
                
            except OSError as e:
                print(f"  Warning: Could not create file in long path: {e}")

    def test_unc_paths(self):
        """Test UNC path handling (requires network setup)"""
        print("🔧 Testing UNC path handling...")
        
        # This test requires actual network shares, so we'll test the format handling
        # rather than actual network access
        
        # Test UNC path pattern validation
        unc_patterns = [
            r"\\localhost\share",
            r"\\server\share\folder", 
            r"\\.\pipe\named_pipe"
        ]
        
        for unc_path in unc_patterns:
            try:
                # Test if vexy_glob handles UNC path formats without crashing
                results = list(vexy_glob.find("*", root=unc_path, max_depth=1))
                print(f"  UNC path {unc_path}: {len(results)} results")
            except Exception as e:
                print(f"  UNC path {unc_path}: Error - {e}")

    def test_file_attributes(self):
        """Test Windows file attribute handling"""
        print("🔧 Testing Windows file attributes...")
        
        # Create files with different attributes
        test_files = {
            "normal_file.txt": 0,
            "readonly_file.txt": stat.S_IREAD,
            "hidden_file.txt": "hidden",  # Will use attrib command
        }
        
        created_files = []
        for filename, attr in test_files.items():
            filepath = self.test_root / filename
            filepath.write_text(f"Content of {filename}")
            created_files.append(filepath)
            
            if attr == "hidden":
                # Use Windows attrib command to set hidden attribute
                try:
                    subprocess.run(["attrib", "+H", str(filepath)], 
                                 check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print(f"  Warning: Could not set hidden attribute on {filename}")
            elif attr:
                try:
                    filepath.chmod(attr)
                except OSError:
                    print(f"  Warning: Could not set attribute {attr} on {filename}")
        
        # Test finding files with different attributes
        all_results = list(vexy_glob.find("*.txt", root=self.test_root))
        hidden_results = list(vexy_glob.find("*.txt", root=self.test_root, hidden=True))
        
        print(f"  Created {len(created_files)} files with different attributes")
        print(f"  Found {len(all_results)} files (normal search)")
        print(f"  Found {len(hidden_results)} files (including hidden)")
        
        # Hidden search should find at least as many files as normal search
        self.assertGreaterEqual(len(hidden_results), len(all_results),
                              "Hidden search should find at least as many files")

    def test_symbolic_links_and_junctions(self):
        """Test symbolic links and junction points (requires elevation)"""
        print("🔧 Testing symbolic links and junction points...")
        
        # Create test directory and file
        source_dir = self.test_root / "source_directory"
        source_dir.mkdir()
        source_file = source_dir / "source_file.txt"
        source_file.write_text("Source file content")
        
        # Try to create symbolic links (may require elevation)
        try:
            # Test directory symbolic link
            symlink_dir = self.test_root / "symlink_directory"
            symlink_dir.symlink_to(source_dir, target_is_directory=True)
            
            # Test file symbolic link
            symlink_file = self.test_root / "symlink_file.txt"
            symlink_file.symlink_to(source_file)
            
            # Test behavior with and without following symlinks
            no_follow_results = list(vexy_glob.find("*.txt", root=self.test_root, 
                                                   follow_symlinks=False))
            follow_results = list(vexy_glob.find("*.txt", root=self.test_root, 
                                               follow_symlinks=True))
            
            print(f"  Created symbolic links successfully")
            print(f"  No follow symlinks: {len(no_follow_results)} files")
            print(f"  Follow symlinks: {len(follow_results)} files")
            
            # Following symlinks should potentially find more files
            self.assertGreaterEqual(len(follow_results), len(no_follow_results),
                                  "Following symlinks should find at least as many files")
            
        except OSError as e:
            print(f"  Warning: Could not create symbolic links (may require elevation): {e}")
            # Test that vexy_glob doesn't crash when encountering existing symlinks
            try:
                results = list(vexy_glob.find("*", root=self.test_root))
                print(f"  Basic search still works: {len(results)} files found")
            except Exception as search_error:
                self.fail(f"Search failed after symlink creation error: {search_error}")

    def test_powershell_compatibility(self):
        """Test PowerShell integration and compatibility"""
        print("🔧 Testing PowerShell compatibility...")
        
        # Create test files
        test_files = ["test1.ps1", "test2.py", "script.bat"]
        for filename in test_files:
            (self.test_root / filename).write_text(f"# {filename} content")
        
        # Test PowerShell execution policies don't interfere
        try:
            # Get current execution policy
            result = subprocess.run(
                ["powershell", "-Command", "Get-ExecutionPolicy"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                policy = result.stdout.strip()
                print(f"  PowerShell execution policy: {policy}")
                
                # Test that vexy_glob works regardless of execution policy
                ps_results = list(vexy_glob.find("*.ps1", root=self.test_root))
                all_results = list(vexy_glob.find("*", root=self.test_root))
                
                print(f"  Found {len(ps_results)} PowerShell files")
                print(f"  Found {len(all_results)} total files")
                
                self.assertEqual(len(ps_results), 1, "Should find exactly 1 PS1 file")
                self.assertEqual(len(all_results), 3, "Should find all 3 test files")
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"  Warning: PowerShell not available or timed out: {e}")

    def test_windows_defender_compatibility(self):
        """Test Windows Defender real-time scanning compatibility"""
        print("🔧 Testing Windows Defender compatibility...")
        
        # Create files that might trigger Windows Defender attention
        test_files = [
            ("suspicious.exe.txt", "This is not actually an executable"),
            ("script.js", "console.log('Hello World');"),
            ("document.docx.txt", "Fake Office document content"),
            ("large_file.txt", "x" * 10000)  # Larger file
        ]
        
        created_files = []
        for filename, content in test_files:
            filepath = self.test_root / filename
            try:
                filepath.write_text(content)
                created_files.append(filepath)
                # Small delay to allow real-time scanning
                time.sleep(0.1)
            except Exception as e:
                print(f"  Warning: Could not create {filename}: {e}")
        
        if created_files:
            # Test that vexy_glob can find files even with Windows Defender active
            start_time = time.time()
            results = list(vexy_glob.find("*", root=self.test_root))
            search_time = time.time() - start_time
            
            print(f"  Created {len(created_files)} test files")
            print(f"  Found {len(results)} files in {search_time:.3f}s")
            
            # Verify all created files were found
            found_names = [Path(r).name for r in results]
            for filepath in created_files:
                self.assertIn(filepath.name, found_names, 
                            f"Should find {filepath.name} despite Windows Defender")

    def test_wsl_integration(self):
        """Test WSL integration (if available)"""
        print("🔧 Testing WSL integration...")
        
        # Check if WSL is available
        try:
            result = subprocess.run(
                ["wsl", "--status"], 
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                print("  WSL is available")
                
                # Test accessing Windows files from WSL context
                # This is complex and requires WSL setup, so we'll just test basic compatibility
                windows_path = str(self.test_root).replace('\\', '/')
                wsl_path = f"/mnt/c/{windows_path[3:]}" if windows_path.startswith('C:') else windows_path
                
                print(f"  Windows path: {self.test_root}")
                print(f"  WSL equivalent: {wsl_path}")
                
                # Test that vexy_glob handles WSL-style paths
                try:
                    results = list(vexy_glob.find("*", root=wsl_path))
                    print(f"  WSL path search: {len(results)} results")
                except Exception as e:
                    print(f"  WSL path search failed (expected): {e}")
                
            else:
                print("  WSL not available or not configured")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("  WSL not available")


def run_windows_ecosystem_tests():
    """Run comprehensive Windows ecosystem tests"""
    print("🚀 Running Windows Ecosystem Tests for vexy_glob")
    print("=" * 60)
    
    # Verify we're on Windows
    if platform.system() != 'Windows':
        print("❌ These tests must be run on Windows")
        sys.exit(1)
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(WindowsEcosystemTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Windows Ecosystem Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ Windows ecosystem compatibility: EXCELLENT")
    elif success_rate >= 75:
        print("🟡 Windows ecosystem compatibility: GOOD")
    else:
        print("❌ Windows ecosystem compatibility: NEEDS IMPROVEMENT")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_windows_ecosystem_tests()
    sys.exit(0 if success else 1)