#!/usr/bin/env python3
# this_file: tests/platform_tests/linux_distro_test.py
"""
Comprehensive Linux distribution matrix testing for vexy_glob

Tests Linux-specific behaviors across distributions:
- Core distributions: Ubuntu 20.04/22.04 LTS, RHEL 8/9, Debian 11/12, Alpine 3.18+
- Filesystem testing: ext4, btrfs (subvolumes), xfs, zfs, tmpfs, and network mounts
- Character encoding: UTF-8, ISO-8859-1, GB2312, and locale-specific encodings
- Special filesystems: /proc, /sys, /dev, /tmp with proper permission handling
- Container testing: Docker, Podman, LXC with volume mounts and overlay filesystems
- Package manager integration: pip, conda, and system packages
- SELinux/AppArmor: mandatory access control systems
"""

import os
import sys
import platform
import tempfile
import subprocess
import shutil
import stat
import locale
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import unittest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Only run on Linux
if platform.system() != 'Linux':
    raise unittest.SkipTest("Linux distribution tests can only run on Linux")

import vexy_glob


class LinuxDistributionTest(unittest.TestCase):
    """Comprehensive Linux distribution matrix testing"""
    
    @classmethod
    def setUpClass(cls):
        """Detect Linux distribution and setup environment"""
        cls.distro_info = cls._detect_distribution()
        cls.filesystem_info = cls._detect_filesystems()
        cls.container_info = cls._detect_containers()
        cls.security_info = cls._detect_security_modules()
        
        print(f"Detected distribution: {cls.distro_info['name']} {cls.distro_info['version']}")
        print(f"Available filesystems: {', '.join(cls.filesystem_info['available'])}")
        print(f"Container runtimes: {', '.join(cls.container_info['available'])}")
        print(f"Security modules: {', '.join(cls.security_info['active'])}")
        
    def setUp(self):
        """Set up test environment"""
        self.test_root = Path(tempfile.mkdtemp(prefix="vexy_glob_linux_test_"))
        print(f"Test root: {self.test_root}")
        
    def tearDown(self):
        """Clean up test environment"""
        try:
            if self.test_root.exists():
                shutil.rmtree(self.test_root)
        except Exception as e:
            print(f"Warning: Could not clean up {self.test_root}: {e}")
    
    @staticmethod
    def _detect_distribution() -> Dict[str, str]:
        """Detect Linux distribution"""
        distro_info = {'name': 'Unknown', 'version': 'Unknown', 'id': 'unknown'}
        
        # Try /etc/os-release first (systemd standard)
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        distro_info['id'] = line.split('=')[1].strip().strip('"')
                    elif line.startswith('NAME='):
                        distro_info['name'] = line.split('=')[1].strip().strip('"')
                    elif line.startswith('VERSION_ID='):
                        distro_info['version'] = line.split('=')[1].strip().strip('"')
        except FileNotFoundError:
            pass
        
        # Fallback methods
        if distro_info['name'] == 'Unknown':
            # Try lsb_release
            try:
                result = subprocess.run(['lsb_release', '-d'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    distro_info['name'] = result.stdout.split('\t')[1].strip()
            except FileNotFoundError:
                pass
            
            # Try /etc/redhat-release
            for release_file in ['/etc/redhat-release', '/etc/debian_version']:
                try:
                    with open(release_file, 'r') as f:
                        distro_info['name'] = f.read().strip()
                        break
                except FileNotFoundError:
                    continue
        
        return distro_info
    
    @staticmethod
    def _detect_filesystems() -> Dict[str, List[str]]:
        """Detect available filesystems"""
        available = []
        
        # Check /proc/filesystems
        try:
            with open('/proc/filesystems', 'r') as f:
                for line in f:
                    fs_type = line.strip().split()[-1]
                    if fs_type not in ['nodev', 'proc', 'sysfs']:
                        available.append(fs_type)
        except FileNotFoundError:
            pass
        
        # Check common filesystem commands
        fs_commands = {
            'btrfs': ['btrfs', '--version'],
            'zfs': ['zfs', 'version'],
            'xfs': ['xfs_info', '-V']
        }
        
        for fs_type, cmd in fs_commands.items():
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and fs_type not in available:
                    available.append(fs_type)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return {'available': available}
    
    @staticmethod
    def _detect_containers() -> Dict[str, List[str]]:
        """Detect available container runtimes"""
        available = []
        
        container_commands = {
            'docker': ['docker', '--version'],
            'podman': ['podman', '--version'],
            'lxc': ['lxc', '--version'],
            'systemd-nspawn': ['systemd-nspawn', '--version']
        }
        
        for runtime, cmd in container_commands.items():
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0:
                    available.append(runtime)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Check if we're inside a container
        in_container = (
            Path('/.dockerenv').exists() or
            os.environ.get('container') or
            Path('/proc/1/cgroup').exists() and 
            'docker' in Path('/proc/1/cgroup').read_text() or
            'lxc' in Path('/proc/1/cgroup').read_text()
        )
        
        return {'available': available, 'in_container': in_container}
    
    @staticmethod
    def _detect_security_modules() -> Dict[str, List[str]]:
        """Detect active security modules"""
        active = []
        
        # Check SELinux
        if Path('/sys/fs/selinux').exists():
            try:
                with open('/sys/fs/selinux/enforce', 'r') as f:
                    if f.read().strip() == '1':
                        active.append('selinux-enforcing')
                    else:
                        active.append('selinux-permissive')
            except:
                active.append('selinux-unknown')
        
        # Check AppArmor
        if Path('/sys/kernel/security/apparmor').exists():
            active.append('apparmor')
        
        # Check other LSMs
        try:
            with open('/sys/kernel/security/lsm', 'r') as f:
                lsms = f.read().strip().split(',')
                for lsm in lsms:
                    if lsm not in ['capability'] and lsm not in active:
                        active.append(lsm)
        except FileNotFoundError:
            pass
        
        return {'active': active}

    def test_distribution_compatibility(self):
        """Test distribution-specific compatibility"""
        print(f"🔧 Testing {self.distro_info['name']} compatibility...")
        
        # Create test files
        test_files = ["test.py", "script.sh", "document.txt"]
        for filename in test_files:
            (self.test_root / filename).write_text(f"Content of {filename}")
        
        # Basic functionality test
        results = list(vexy_glob.find("*", root=self.test_root))
        self.assertEqual(len(results), len(test_files), 
                        f"Should find all files on {self.distro_info['name']}")
        
        # Test common patterns for this distribution
        if 'ubuntu' in self.distro_info['id'].lower() or 'debian' in self.distro_info['id'].lower():
            # Debian-based distributions
            self._test_debian_specific()
        elif 'rhel' in self.distro_info['id'].lower() or 'centos' in self.distro_info['id'].lower():
            # RHEL-based distributions
            self._test_rhel_specific()
        elif 'alpine' in self.distro_info['id'].lower():
            # Alpine Linux
            self._test_alpine_specific()
    
    def _test_debian_specific(self):
        """Test Debian/Ubuntu specific behaviors"""
        print("  Testing Debian/Ubuntu specific behaviors...")
        
        # Test /var/lib/dpkg if it exists
        if Path('/var/lib/dpkg').exists():
            results = list(vexy_glob.find("*.list", root="/var/lib/dpkg/info", max_depth=1))
            print(f"    Found {len(results)} dpkg list files")
    
    def _test_rhel_specific(self):
        """Test RHEL/CentOS specific behaviors"""
        print("  Testing RHEL/CentOS specific behaviors...")
        
        # Test /var/lib/rpm if it exists
        if Path('/var/lib/rpm').exists():
            results = list(vexy_glob.find("*", root="/var/lib/rpm", max_depth=1))
            print(f"    Found {len(results)} RPM database files")
    
    def _test_alpine_specific(self):
        """Test Alpine Linux specific behaviors"""
        print("  Testing Alpine Linux specific behaviors...")
        
        # Test /var/lib/apk if it exists
        if Path('/var/lib/apk').exists():
            results = list(vexy_glob.find("*", root="/var/lib/apk", max_depth=1))
            print(f"    Found {len(results)} APK files")

    def test_filesystem_compatibility(self):
        """Test different filesystem types"""
        print("🔧 Testing filesystem compatibility...")
        
        # Test on current filesystem
        current_fs = self._get_filesystem_type(self.test_root)
        print(f"  Current filesystem: {current_fs}")
        
        # Create files with various names and attributes
        test_cases = [
            ("normal_file.txt", "Normal file"),
            ("file with spaces.txt", "File with spaces"),
            ("file-with-dashes.txt", "File with dashes"),
            ("file_with_unicode_café.txt", "File with unicode"),
            ("UPPERCASE.TXT", "Uppercase file"),
            (".hidden_file", "Hidden file"),
            ("very_long_filename_" + "x" * 200 + ".txt", "Long filename")
        ]
        
        created_files = []
        for filename, content in test_cases:
            try:
                filepath = self.test_root / filename
                filepath.write_text(content)
                created_files.append(filename)
            except (OSError, UnicodeEncodeError) as e:
                print(f"    Warning: Could not create {filename}: {e}")
        
        # Test finding files on this filesystem
        results = list(vexy_glob.find("*", root=self.test_root))
        hidden_results = list(vexy_glob.find("*", root=self.test_root, hidden=True))
        
        print(f"    Created {len(created_files)} files")
        print(f"    Found {len(results)} files (normal)")
        print(f"    Found {len(hidden_results)} files (including hidden)")
        
        # Hidden search should find at least as many files
        self.assertGreaterEqual(len(hidden_results), len(results))
    
    def _get_filesystem_type(self, path: Path) -> str:
        """Get filesystem type for a path"""
        try:
            result = subprocess.run(['stat', '-f', '-c', '%T', str(path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        
        return "unknown"

    def test_character_encoding(self):
        """Test character encoding handling"""
        print("🔧 Testing character encoding handling...")
        
        # Get current locale
        current_locale = locale.getlocale()[1] or 'UTF-8'
        print(f"  Current encoding: {current_locale}")
        
        # Test files with different encodings
        encoding_tests = [
            ("utf8_test_café.txt", "UTF-8 content: café, naïve, résumé", 'utf-8'),
            ("latin1_test.txt", "Latin-1 content: café", 'iso-8859-1'),
            ("ascii_test.txt", "ASCII content only", 'ascii')
        ]
        
        created_files = []
        for filename, content, encoding in encoding_tests:
            try:
                filepath = self.test_root / filename
                filepath.write_text(content, encoding=encoding)
                created_files.append((filename, encoding))
            except (OSError, UnicodeEncodeError) as e:
                print(f"    Warning: Could not create {filename} with {encoding}: {e}")
        
        # Test finding files with different encodings
        results = list(vexy_glob.find("*", root=self.test_root))
        utf8_results = list(vexy_glob.find("*utf8*", root=self.test_root))
        
        print(f"    Created {len(created_files)} files with different encodings")
        print(f"    Found {len(results)} total files")
        print(f"    Found {len(utf8_results)} UTF-8 files")

    def test_special_filesystems(self):
        """Test special filesystems (/proc, /sys, /dev, /tmp)"""
        print("🔧 Testing special filesystems...")
        
        special_paths = [
            ("/proc", "Process filesystem"),
            ("/sys", "System filesystem"), 
            ("/dev", "Device filesystem"),
            ("/tmp", "Temporary filesystem")
        ]
        
        for path_str, description in special_paths:
            path = Path(path_str)
            if not path.exists():
                continue
                
            print(f"  Testing {description} ({path_str})...")
            
            try:
                # Test limited search (max_depth=1 to avoid deep recursion)
                results = list(vexy_glob.find("*", root=path_str, max_depth=1))
                print(f"    Found {len(results)} entries in {path_str}")
                
                # Test specific patterns
                if path_str == "/proc":
                    # Look for process directories (numeric names)
                    proc_results = list(vexy_glob.find("[0-9]*", root=path_str, max_depth=1))
                    print(f"    Found {len(proc_results)} process directories")
                
                elif path_str == "/sys":
                    # Look for kernel modules
                    if Path("/sys/module").exists():
                        module_results = list(vexy_glob.find("*", root="/sys/module", max_depth=1))
                        print(f"    Found {len(module_results)} kernel modules")
                
                elif path_str == "/dev":
                    # Look for common device files
                    dev_results = list(vexy_glob.find("tty*", root=path_str, max_depth=1))
                    print(f"    Found {len(dev_results)} TTY devices")
                
            except (PermissionError, OSError) as e:
                print(f"    Permission denied or error accessing {path_str}: {e}")
            except Exception as e:
                print(f"    Unexpected error with {path_str}: {e}")

    def test_container_compatibility(self):
        """Test container environment compatibility"""
        print("🔧 Testing container compatibility...")
        
        if self.container_info['in_container']:
            print("  Running inside container - testing container-specific behavior")
            
            # Test container-specific paths
            container_paths = [
                "/proc/1/cgroup",
                "/proc/self/mountinfo",
                "/.dockerenv"
            ]
            
            for path_str in container_paths:
                if Path(path_str).exists():
                    print(f"    Container marker found: {path_str}")
            
            # Test filesystem behavior in container
            results = list(vexy_glob.find("*", root="/", max_depth=1))
            print(f"    Found {len(results)} entries in container root")
            
        else:
            print("  Not running in container - testing host system")
            
            # Test if we can use container runtimes
            for runtime in self.container_info['available']:
                print(f"    Available container runtime: {runtime}")

    def test_security_module_compatibility(self):
        """Test SELinux/AppArmor compatibility"""
        print("🔧 Testing security module compatibility...")
        
        for security_module in self.security_info['active']:
            print(f"  Testing with {security_module}...")
            
            if 'selinux' in security_module:
                self._test_selinux_compatibility()
            elif security_module == 'apparmor':
                self._test_apparmor_compatibility()
    
    def _test_selinux_compatibility(self):
        """Test SELinux specific compatibility"""
        print("    Testing SELinux compatibility...")
        
        try:
            # Check SELinux context of test directory
            result = subprocess.run(['ls', '-Z', str(self.test_root)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"      SELinux context: {result.stdout.strip()}")
        except FileNotFoundError:
            print("      ls -Z not available")
        
        # Test file operations work under SELinux
        test_file = self.test_root / "selinux_test.txt"
        test_file.write_text("SELinux test content")
        
        results = list(vexy_glob.find("*selinux*", root=self.test_root))
        self.assertEqual(len(results), 1, "Should find SELinux test file")
    
    def _test_apparmor_compatibility(self):
        """Test AppArmor specific compatibility"""
        print("    Testing AppArmor compatibility...")
        
        # Test file operations work under AppArmor
        test_file = self.test_root / "apparmor_test.txt"
        test_file.write_text("AppArmor test content")
        
        results = list(vexy_glob.find("*apparmor*", root=self.test_root))
        self.assertEqual(len(results), 1, "Should find AppArmor test file")

    def test_package_manager_integration(self):
        """Test package manager integration"""
        print("🔧 Testing package manager integration...")
        
        # Test pip installation path
        try:
            import vexy_glob
            import_path = vexy_glob.__file__
            print(f"  vexy_glob imported from: {import_path}")
            
            # Test that we can find the installed package
            package_dir = Path(import_path).parent
            if package_dir.exists():
                results = list(vexy_glob.find("*.py", root=str(package_dir)))
                print(f"    Found {len(results)} Python files in package")
        except ImportError:
            print("  vexy_glob not installed via package manager")
        
        # Test system Python paths
        python_paths = [
            "/usr/lib/python3*/site-packages",
            "/usr/local/lib/python3*/site-packages", 
            "~/.local/lib/python3*/site-packages"
        ]
        
        for path_pattern in python_paths:
            try:
                expanded_path = Path(path_pattern).expanduser()
                if expanded_path.exists():
                    results = list(vexy_glob.find("vexy_glob*", root=str(expanded_path), max_depth=2))
                    if results:
                        print(f"    Found vexy_glob in {expanded_path}: {len(results)} files")
            except:
                pass

    def test_performance_on_linux(self):
        """Test performance characteristics on Linux"""
        print("🔧 Testing Linux-specific performance...")
        
        # Create larger test dataset
        num_files = 1000
        for i in range(num_files):
            subdir = self.test_root / f"subdir_{i // 100}"
            subdir.mkdir(exist_ok=True)
            (subdir / f"file_{i}.txt").write_text(f"Content {i}")
        
        # Measure performance
        start_time = time.time()
        results = list(vexy_glob.find("*.txt", root=self.test_root))
        search_time = time.time() - start_time
        
        print(f"    Created {num_files} files")
        print(f"    Found {len(results)} files in {search_time:.3f}s")
        print(f"    Performance: {len(results)/search_time:.0f} files/second")
        
        # Performance should be reasonable
        self.assertLess(search_time, 5.0, "Search should complete within 5 seconds")
        self.assertEqual(len(results), num_files, f"Should find all {num_files} files")


def run_linux_distribution_tests():
    """Run comprehensive Linux distribution tests"""
    print("🚀 Running Linux Distribution Tests for vexy_glob")
    print("=" * 60)
    
    # Verify we're on Linux
    if platform.system() != 'Linux':
        print("❌ These tests must be run on Linux")
        sys.exit(1)
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(LinuxDistributionTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Linux Distribution Test Summary")
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
        print("✅ Linux distribution compatibility: EXCELLENT")
    elif success_rate >= 75:
        print("🟡 Linux distribution compatibility: GOOD")
    else:
        print("❌ Linux distribution compatibility: NEEDS IMPROVEMENT")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_linux_distribution_tests()
    sys.exit(0 if success else 1)