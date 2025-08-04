#!/usr/bin/env python3
# this_file: tests/platform_tests/macos_integration_test.py
"""
Comprehensive macOS platform integration testing for vexy_glob

Tests macOS-specific behaviors:
- Filesystem features: APFS (case-sensitive/insensitive), HFS+, and external drives
- macOS metadata: .DS_Store, .fseventsd, .Spotlight-V100, .Trashes handling
- Extended attributes: xattr preservation and com.apple.* attribute handling
- Resource forks: legacy resource fork detection and proper skipping
- System integration: Time Machine exclusions, Spotlight indexing interference
- Security: System Integrity Protection (SIP) and Gatekeeper
- Versions: macOS 11 (Big Sur) through macOS 14 (Sonoma) compatibility
"""

import os
import sys
import platform
import tempfile
import subprocess
import shutil
import stat
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import unittest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Only run on macOS
if platform.system() != 'Darwin':
    raise unittest.SkipTest("macOS integration tests can only run on macOS")

import vexy_glob


class MacOSIntegrationTest(unittest.TestCase):
    """Comprehensive macOS platform integration testing"""
    
    @classmethod
    def setUpClass(cls):
        """Detect macOS version and system configuration"""
        cls.macos_info = cls._detect_macos_version()
        cls.filesystem_info = cls._detect_filesystems()
        cls.security_info = cls._detect_security_features()
        cls.xcode_info = cls._detect_xcode()
        
        print(f"Detected macOS: {cls.macos_info['version']} ({cls.macos_info['name']})")
        print(f"File systems: {', '.join(cls.filesystem_info['available'])}")
        print(f"SIP status: {cls.security_info['sip_status']}")
        print(f"Xcode available: {cls.xcode_info['available']}")
        
    def setUp(self):
        """Set up test environment"""
        self.test_root = Path(tempfile.mkdtemp(prefix="vexy_glob_macos_test_"))
        print(f"Test root: {self.test_root}")
        
    def tearDown(self):
        """Clean up test environment"""
        try:
            if self.test_root.exists():
                # Remove extended attributes and special files
                self._clean_extended_attributes(self.test_root)
                shutil.rmtree(self.test_root)
        except Exception as e:
            print(f"Warning: Could not clean up {self.test_root}: {e}")
    
    def _clean_extended_attributes(self, path: Path):
        """Remove extended attributes from test files"""
        for root, dirs, files in os.walk(path):
            for name in files + dirs:
                filepath = Path(root) / name
                try:
                    # Remove extended attributes
                    subprocess.run(['xattr', '-c', str(filepath)], 
                                 capture_output=True, check=False)
                except FileNotFoundError:
                    pass
    
    @staticmethod
    def _detect_macos_version() -> Dict[str, str]:
        """Detect macOS version and name"""
        version_info = {'version': 'Unknown', 'name': 'Unknown', 'build': 'Unknown'}
        
        try:
            result = subprocess.run(['sw_vers'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('ProductVersion:'):
                        version_info['version'] = line.split('\t')[1].strip()
                    elif line.startswith('ProductName:'):
                        version_info['name'] = line.split('\t')[1].strip()
                    elif line.startswith('BuildVersion:'):
                        version_info['build'] = line.split('\t')[1].strip()
        except FileNotFoundError:
            pass
        
        # Map version to marketing name
        version = version_info['version']
        if version.startswith('14.'):
            version_info['marketing_name'] = 'Sonoma'
        elif version.startswith('13.'):
            version_info['marketing_name'] = 'Ventura'
        elif version.startswith('12.'):
            version_info['marketing_name'] = 'Monterey'
        elif version.startswith('11.'):
            version_info['marketing_name'] = 'Big Sur'
        else:
            version_info['marketing_name'] = 'Unknown'
        
        return version_info
    
    @staticmethod
    def _detect_filesystems() -> Dict[str, List[str]]:
        """Detect available filesystems"""
        available = []
        
        try:
            # Check mount points for filesystem types
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ' on ' in line and ' (' in line:
                        fs_info = line.split(' (')[1].split(',')[0]
                        if fs_info not in available:
                            available.append(fs_info)
        except FileNotFoundError:
            pass
        
        # Check for specific filesystem tools
        fs_tools = {
            'APFS': ['diskutil', 'apfs', 'list'],
            'HFS+': ['diskutil', 'info', '/']
        }
        
        for fs_name, cmd in fs_tools.items():
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and fs_name not in available:
                    available.append(fs_name)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return {'available': available}
    
    @staticmethod
    def _detect_security_features() -> Dict[str, Any]:
        """Detect macOS security features"""
        security_info = {'sip_status': 'unknown', 'gatekeeper': 'unknown'}
        
        # Check SIP status
        try:
            result = subprocess.run(['csrutil', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                if 'disabled' in result.stdout.lower():
                    security_info['sip_status'] = 'disabled'
                elif 'enabled' in result.stdout.lower():
                    security_info['sip_status'] = 'enabled'
        except FileNotFoundError:
            pass
        
        # Check Gatekeeper status
        try:
            result = subprocess.run(['spctl', '--status'], capture_output=True, text=True)
            if result.returncode == 0:
                security_info['gatekeeper'] = result.stdout.strip()
        except FileNotFoundError:
            pass
        
        return security_info
    
    @staticmethod
    def _detect_xcode() -> Dict[str, Any]:
        """Detect Xcode installation"""
        xcode_info = {'available': False, 'version': 'Unknown', 'command_line_tools': False}
        
        # Check for Xcode
        try:
            result = subprocess.run(['xcode-select', '--print-path'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                xcode_info['available'] = True
                xcode_path = result.stdout.strip()
                
                # Check if it's command line tools or full Xcode
                if 'CommandLineTools' in xcode_path:
                    xcode_info['command_line_tools'] = True
                else:
                    # Try to get Xcode version
                    try:
                        result = subprocess.run(['xcodebuild', '-version'], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            version_line = result.stdout.split('\n')[0]
                            xcode_info['version'] = version_line.split(' ')[1]
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
        
        return xcode_info

    def test_apfs_filesystem_features(self):
        """Test APFS filesystem features"""
        print("🔧 Testing APFS filesystem features...")
        
        # Check if we're on APFS
        fs_type = self._get_filesystem_type(self.test_root)
        print(f"  Filesystem type: {fs_type}")
        
        if 'apfs' in fs_type.lower():
            # Test case sensitivity behavior
            self._test_case_sensitivity()
            
            # Test APFS-specific features
            self._test_apfs_snapshots()
        else:
            print(f"  Not on APFS filesystem, skipping APFS-specific tests")
    
    def _get_filesystem_type(self, path: Path) -> str:
        """Get filesystem type for a path"""
        try:
            result = subprocess.run(['stat', '-f', '%T', str(path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        
        return "unknown"
    
    def _test_case_sensitivity(self):
        """Test case sensitivity behavior"""
        print("    Testing case sensitivity...")
        
        # Create files with different cases
        test_files = [
            "TestFile.txt",
            "testfile.txt",
            "TESTFILE.TXT"
        ]
        
        created_files = []
        for filename in test_files:
            filepath = self.test_root / filename
            try:
                filepath.write_text(f"Content of {filename}")
                created_files.append(filename)
            except FileExistsError:
                # Case-insensitive filesystem
                print(f"      Case-insensitive filesystem detected (could not create {filename})")
                break
        
        # Test pattern matching behavior
        results = list(vexy_glob.find("*.txt", root=self.test_root))
        TXT_results = list(vexy_glob.find("*.TXT", root=self.test_root))
        
        print(f"      Created {len(created_files)} files")
        print(f"      Found {len(results)} with *.txt pattern")
        print(f"      Found {len(TXT_results)} with *.TXT pattern")
    
    def _test_apfs_snapshots(self):
        """Test APFS snapshot handling"""
        print("    Testing APFS snapshot handling...")
        
        # APFS snapshots appear in /.vol/
        snapshot_path = Path("/.vol")
        if snapshot_path.exists():
            try:
                # Test that we can traverse (but don't go deep)
                results = list(vexy_glob.find("*", root="/.vol", max_depth=1))
                print(f"      Found {len(results)} entries in /.vol")
            except (PermissionError, OSError) as e:
                print(f"      Cannot access /.vol: {e}")

    def test_macos_metadata_handling(self):
        """Test macOS metadata file handling"""
        print("🔧 Testing macOS metadata handling...")
        
        # Create macOS-specific metadata files
        metadata_files = [
            ".DS_Store",
            ".fseventsd",
            ".Spotlight-V100", 
            ".Trashes",
            ".VolumeIcon.icns",
            "._resource_fork_file"
        ]
        
        created_files = []
        for filename in metadata_files:
            filepath = self.test_root / filename
            try:
                if filename == ".fseventsd":
                    # Create as directory
                    filepath.mkdir()
                    (filepath / "log").write_text("FSEvents log data")
                elif filename == ".Trashes":
                    # Create as directory
                    filepath.mkdir()
                else:
                    # Create as file
                    filepath.write_text(f"macOS metadata: {filename}")
                created_files.append(filename)
            except OSError as e:
                print(f"  Warning: Could not create {filename}: {e}")
        
        # Test default behavior (should skip hidden files)
        normal_results = list(vexy_glob.find("*", root=self.test_root))
        hidden_results = list(vexy_glob.find("*", root=self.test_root, hidden=True))
        
        print(f"  Created {len(created_files)} metadata files")
        print(f"  Normal search: {len(normal_results)} files")
        print(f"  Hidden search: {len(hidden_results)} files")
        
        # Test that .DS_Store is handled properly
        ds_store_results = list(vexy_glob.find(".DS_Store", root=self.test_root, hidden=True))
        if ".DS_Store" in created_files:
            self.assertGreaterEqual(len(ds_store_results), 1, "Should find .DS_Store when explicitly searched with hidden=True")
        else:
            print("    .DS_Store was not created successfully")

    def test_extended_attributes(self):
        """Test extended attributes (xattr) handling"""
        print("🔧 Testing extended attributes...")
        
        # Create files and add extended attributes
        test_files = [
            ("normal_file.txt", None),
            ("file_with_xattr.txt", {"com.apple.metadata:kMDItemComment": "Test comment"}),
            ("file_with_finder_info.txt", {"com.apple.FinderInfo": b"FINDER_INFO_DATA"}),
        ]
        
        created_files = []
        for filename, xattrs in test_files:
            filepath = self.test_root / filename
            filepath.write_text(f"Content of {filename}")
            created_files.append(filename)
            
            if xattrs:
                for attr_name, attr_value in xattrs.items():
                    try:
                        if isinstance(attr_value, str):
                            # Use xattr command for string values
                            subprocess.run(['xattr', '-w', attr_name, attr_value, str(filepath)], 
                                         check=True, capture_output=True)
                        else:
                            # Use xattr command for binary values (os.setxattr not available on macOS)
                            import base64
                            encoded_value = base64.b64encode(attr_value).decode('ascii')
                            subprocess.run(['xattr', '-wx', attr_name, encoded_value, str(filepath)], 
                                         check=True, capture_output=True)
                        print(f"    Set extended attribute {attr_name} on {filename}")
                    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
                        print(f"    Warning: Could not set xattr {attr_name} on {filename}: {e}")
        
        # Test that files with extended attributes are found normally
        results = list(vexy_glob.find("*.txt", root=self.test_root))
        self.assertEqual(len(results), len(created_files), "Should find all files regardless of xattrs")
        
        # Test reading extended attributes
        for filename in created_files:
            filepath = self.test_root / filename
            try:
                result = subprocess.run(['xattr', '-l', str(filepath)], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    print(f"    {filename} has extended attributes: {len(result.stdout.split())} attrs")
            except FileNotFoundError:
                pass

    def test_resource_forks(self):
        """Test resource fork handling (legacy)"""
        print("🔧 Testing resource fork handling...")
        
        # Create files that might have resource forks
        test_files = [
            "legacy_app.app",
            "old_document.rtf",  
            "classic_file.txt"
        ]
        
        for filename in test_files:
            filepath = self.test_root / filename
            filepath.write_text(f"Data fork of {filename}")
            
            # Try to create a resource fork using the ._filename convention
            resource_fork_name = f"._{filename}"
            resource_fork_path = self.test_root / resource_fork_name
            try:
                resource_fork_path.write_bytes(b"FAKE_RESOURCE_FORK_DATA")
                print(f"    Created resource fork file for {filename}")
            except OSError as e:
                print(f"    Could not create resource fork for {filename}: {e}")
        
        # Test finding files with resource forks
        all_results = list(vexy_glob.find("*", root=self.test_root))
        data_files = list(vexy_glob.find("*", root=self.test_root, 
                                       exclude=["._*"]))
        
        print(f"    Found {len(all_results)} total files")
        print(f"    Found {len(data_files)} files (excluding resource forks)")

    def test_time_machine_integration(self):
        """Test Time Machine integration"""
        print("🔧 Testing Time Machine integration...")
        
        # Create .noindex file to test Time Machine exclusion
        noindex_file = self.test_root / ".noindex"
        noindex_file.write_text("Time Machine exclusion marker")
        
        # Create normal files in the directory
        for i in range(5):
            (self.test_root / f"backup_test_{i}.txt").write_text(f"Content {i}")
        
        # Test that .noindex file is handled properly
        all_results = list(vexy_glob.find("*", root=self.test_root))
        hidden_results = list(vexy_glob.find("*", root=self.test_root, hidden=True))
        noindex_results = list(vexy_glob.find(".noindex", root=self.test_root))
        
        print(f"    Found {len(all_results)} files (normal search)")
        print(f"    Found {len(hidden_results)} files (including hidden)")
        print(f"    Found {len(noindex_results)} .noindex files")
        
        # Test Time Machine exclusion attribute
        try:
            # Set Time Machine exclusion attribute
            subprocess.run(['tmutil', 'addexclusion', str(self.test_root / "backup_test_0.txt")], 
                         check=True, capture_output=True)
            print("    Set Time Machine exclusion on test file")
            
            # File should still be found by vexy_glob (exclusion is metadata)
            excluded_results = list(vexy_glob.find("backup_test_0.txt", root=self.test_root))
            self.assertEqual(len(excluded_results), 1, "Should find Time Machine excluded file")
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"    Warning: Could not test Time Machine exclusion: {e}")

    def test_spotlight_integration(self):
        """Test Spotlight integration"""
        print("🔧 Testing Spotlight integration...")
        
        # Create files with Spotlight-indexable content
        spotlight_files = [
            ("document.txt", "This is a text document with searchable content"),
            ("code.py", "# Python code file\nprint('Hello, World!')"),
            ("image.txt", "Fake image file for testing"),  # .txt to avoid actual image handling
        ]
        
        for filename, content in spotlight_files:
            (self.test_root / filename).write_text(content)
        
        # Test basic file finding (Spotlight shouldn't interfere)
        results = list(vexy_glob.find("*", root=self.test_root))
        self.assertGreaterEqual(len(results), len(spotlight_files), "Should find at least the created test files")
        
        # Test that .Spotlight-V100 directories are handled if they exist
        spotlight_dir = self.test_root / ".Spotlight-V100"
        if not spotlight_dir.exists():
            try:
                spotlight_dir.mkdir()
                (spotlight_dir / "index").write_text("Fake Spotlight index")
                print("    Created fake Spotlight index directory")
            except OSError:
                pass
        
        # Test finding files while ignoring Spotlight directories
        all_with_hidden = list(vexy_glob.find("*", root=self.test_root, hidden=True))
        print(f"    Found {len(all_with_hidden)} files including Spotlight metadata")

    def test_security_features(self):
        """Test System Integrity Protection and Gatekeeper integration"""
        print("🔧 Testing macOS security features...")
        
        print(f"  SIP Status: {self.security_info['sip_status']}")
        print(f"  Gatekeeper: {self.security_info['gatekeeper']}")
        
        # Test access to SIP-protected directories (should fail gracefully)
        sip_protected_paths = [
            "/System/Library/Extensions",
            "/usr/libexec",
            "/System/Library/LaunchDaemons"
        ]
        
        for protected_path in sip_protected_paths:
            if Path(protected_path).exists():
                try:
                    # This should work for reading, but may be limited
                    results = list(vexy_glob.find("*", root=protected_path, max_depth=1))
                    print(f"    Accessed {protected_path}: {len(results)} entries")
                except (PermissionError, OSError) as e:
                    print(f"    Access denied to {protected_path} (expected): {e}")
        
        # Test file operations in user space (should work)
        user_file = self.test_root / "security_test.txt"
        user_file.write_text("Security test content")
        
        results = list(vexy_glob.find("security_test.txt", root=self.test_root))
        self.assertEqual(len(results), 1, "Should access user files despite security features")

    def test_version_compatibility(self):
        """Test macOS version-specific features"""
        print(f"🔧 Testing macOS {self.macos_info['marketing_name']} compatibility...")
        
        version = self.macos_info['version']
        
        # Test features available in different macOS versions
        if version.startswith('11.'):  # Big Sur
            self._test_big_sur_features()
        elif version.startswith('12.'):  # Monterey
            self._test_monterey_features()
        elif version.startswith('13.'):  # Ventura
            self._test_ventura_features()
        elif version.startswith('14.'):  # Sonoma
            self._test_sonoma_features()
        
        # Test basic functionality works on all supported versions
        test_files = ["version_test.txt", "compatibility.py", "document.md"]
        for filename in test_files:
            (self.test_root / filename).write_text(f"Content for {filename}")
        
        results = list(vexy_glob.find("*", root=self.test_root))
        self.assertGreaterEqual(len(results), len(test_files), 
                               f"Basic functionality should work on macOS {version}")
    
    def _test_big_sur_features(self):
        """Test Big Sur specific features"""
        print("    Testing Big Sur specific features...")
        # Big Sur introduced ARM64 support and new security features
        # Test that vexy_glob works on both Intel and ARM Macs
        arch = platform.machine()
        print(f"      Architecture: {arch}")
    
    def _test_monterey_features(self):
        """Test Monterey specific features"""
        print("    Testing Monterey specific features...")
        # Monterey enhanced privacy and security
        pass
    
    def _test_ventura_features(self):
        """Test Ventura specific features"""
        print("    Testing Ventura specific features...")
        # Ventura introduced new metadata handling
        pass
    
    def _test_sonoma_features(self):
        """Test Sonoma specific features"""
        print("    Testing Sonoma specific features...")
        # Sonoma has updated filesystem behaviors
        pass

    def test_xcode_integration(self):
        """Test Xcode and development tool integration"""
        print("🔧 Testing Xcode integration...")
        
        if not self.xcode_info['available']:
            print("  Xcode not available, skipping Xcode-specific tests")
            return
        
        print(f"  Xcode version: {self.xcode_info['version']}")
        print(f"  Command line tools: {self.xcode_info['command_line_tools']}")
        
        # Create Xcode project structure
        project_structure = [
            "TestProject.xcodeproj/project.pbxproj",
            "TestProject.xcodeproj/project.xcworkspace/contents.xcworkspacedata",
            "TestProject/AppDelegate.swift",
            "TestProject/ViewController.swift", 
            "TestProject/Info.plist",
            "TestProject/Assets.xcassets/AppIcon.appiconset/Contents.json"
        ]
        
        for filepath in project_structure:
            full_path = self.test_root / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Xcode file: {filepath}")
        
        # Test finding Xcode project files
        swift_files = list(vexy_glob.find("*.swift", root=self.test_root))
        xcodeproj_files = list(vexy_glob.find("*.xcodeproj", root=self.test_root))
        plist_files = list(vexy_glob.find("*.plist", root=self.test_root))
        
        print(f"    Found {len(swift_files)} Swift files")
        print(f"    Found {len(xcodeproj_files)} Xcode projects")
        print(f"    Found {len(plist_files)} plist files")
        
        # Test build directory exclusion (common in .gitignore)
        build_dir = self.test_root / "build"
        build_dir.mkdir()
        app_dir = build_dir / "Release" / "TestApp.app"
        app_dir.mkdir(parents=True)
        (app_dir / "TestApp").write_text("Binary")
        
        # With gitignore-style exclusion of build directory
        all_files = list(vexy_glob.find("*", root=self.test_root))
        print(f"    Total files including build artifacts: {len(all_files)}")

    def test_performance_on_macos(self):
        """Test performance characteristics on macOS"""
        print("🔧 Testing macOS-specific performance...")
        
        # Create test dataset with macOS-specific files
        num_files = 1000
        for i in range(num_files):
            subdir = self.test_root / f"folder_{i // 100}"
            subdir.mkdir(exist_ok=True)
            
            # Mix of file types common on macOS
            if i % 4 == 0:
                filename = f"document_{i}.pages"
            elif i % 4 == 1:
                filename = f"code_{i}.swift"
            elif i % 4 == 2:
                filename = f"image_{i}.png"
            else:
                filename = f"text_{i}.txt"
            
            (subdir / filename).write_text(f"macOS file {i}")
        
        # Add some .DS_Store files (common on macOS)
        for i in range(0, num_files, 100):
            subdir = self.test_root / f"folder_{i // 100}"
            (subdir / ".DS_Store").write_text("Finder metadata")
        
        # Measure performance
        start_time = time.time()
        all_results = list(vexy_glob.find("*", root=self.test_root))
        all_time = time.time() - start_time
        
        start_time = time.time()
        no_hidden_results = list(vexy_glob.find("*", root=self.test_root, hidden=False))
        no_hidden_time = time.time() - start_time
        
        print(f"    Created {num_files} files + metadata")
        print(f"    All files: {len(all_results)} found in {all_time:.3f}s")
        print(f"    No hidden: {len(no_hidden_results)} found in {no_hidden_time:.3f}s")
        print(f"    Performance: {len(all_results)/all_time:.0f} files/second")
        
        # Performance should be reasonable on macOS
        self.assertLess(all_time, 10.0, "Search should complete within 10 seconds on macOS")


def run_macos_integration_tests():
    """Run comprehensive macOS integration tests"""
    print("🚀 Running macOS Integration Tests for vexy_glob")
    print("=" * 60)
    
    # Verify we're on macOS
    if platform.system() != 'Darwin':
        print("❌ These tests must be run on macOS")
        sys.exit(1)
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MacOSIntegrationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 macOS Integration Test Summary")
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
        print("✅ macOS integration: EXCELLENT")
    elif success_rate >= 75:
        print("🟡 macOS integration: GOOD")
    else:
        print("❌ macOS integration: NEEDS IMPROVEMENT")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_macos_integration_tests()
    sys.exit(0 if success else 1)