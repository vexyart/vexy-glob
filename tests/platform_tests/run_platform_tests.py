#!/usr/bin/env python3
# this_file: tests/platform_tests/run_platform_tests.py
"""
Master platform testing coordinator for vexy_glob

Runs comprehensive platform tests across Windows, Linux, and macOS.
Generates detailed compatibility reports and identifies platform-specific issues.
"""

import os
import sys
import platform
import argparse
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import vexy_glob
except ImportError as e:
    print(f"❌ Could not import vexy_glob: {e}")
    print("Make sure vexy_glob is installed: pip install -e .")
    sys.exit(1)


class PlatformTestCoordinator:
    """Coordinates platform-specific testing"""
    
    def __init__(self):
        self.current_platform = platform.system()
        self.test_results = {}
        self.start_time = time.time()
        
    def detect_environment(self) -> Dict[str, Any]:
        """Detect current environment details"""
        env_info = {
            'platform': self.current_platform,
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
        }
        
        # Platform-specific details
        if self.current_platform == 'Windows':
            env_info['windows_edition'] = platform.win32_edition()
            env_info['windows_version'] = platform.win32_ver()
        elif self.current_platform == 'Darwin':
            env_info['macos_version'] = platform.mac_ver()
        elif self.current_platform == 'Linux':
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('ID='):
                            env_info['linux_distro'] = line.split('=')[1].strip().strip('"')
                        elif line.startswith('VERSION_ID='):
                            env_info['linux_version'] = line.split('=')[1].strip().strip('"')
            except FileNotFoundError:
                pass
        
        # Check vexy_glob installation
        try:
            env_info['vexy_glob_version'] = getattr(vexy_glob, '__version__', 'unknown')
            env_info['vexy_glob_path'] = vexy_glob.__file__
        except:
            env_info['vexy_glob_version'] = 'unknown'
            env_info['vexy_glob_path'] = 'unknown'
        
        return env_info
    
    def run_basic_functionality_tests(self) -> Dict[str, Any]:
        """Run basic functionality tests that work on all platforms"""
        print("🔧 Running basic functionality tests...")
        
        import tempfile
        import shutil
        
        results = {
            'basic_file_finding': False,
            'pattern_matching': False,
            'content_search': False,
            'streaming': False,
            'error_count': 0,
            'errors': []
        }
        
        test_root = None
        try:
            # Create test environment
            test_root = Path(tempfile.mkdtemp(prefix="vexy_glob_basic_test_"))
            
            # Create test files
            test_files = [
                ("test.py", "print('hello world')"),
                ("document.txt", "This is a test document"),
                ("script.sh", "#!/bin/bash\necho 'test'"),
                ("data.json", '{"test": true}'),
                ("subdir/nested.py", "# nested file"),
            ]
            
            for filepath, content in test_files:
                full_path = test_root / filepath
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            
            # Test 1: Basic file finding
            try:
                files = list(vexy_glob.find("*", root=str(test_root)))
                if len(files) >= len(test_files):
                    results['basic_file_finding'] = True
                else:
                    results['errors'].append(f"Expected {len(test_files)} files, found {len(files)}")
            except Exception as e:
                results['errors'].append(f"Basic file finding failed: {e}")
                results['error_count'] += 1
            
            # Test 2: Pattern matching
            try:
                py_files = list(vexy_glob.find("*.py", root=str(test_root)))
                if len(py_files) >= 2:  # test.py and nested.py
                    results['pattern_matching'] = True
                else:
                    results['errors'].append(f"Pattern matching: expected 2+ .py files, found {len(py_files)}")
            except Exception as e:
                results['errors'].append(f"Pattern matching failed: {e}")
                results['error_count'] += 1
            
            # Test 3: Content search
            try:
                search_results = list(vexy_glob.search("test", "*", str(test_root)))
                if len(search_results) > 0:
                    results['content_search'] = True
                else:
                    results['errors'].append("Content search returned no results")
            except Exception as e:
                results['errors'].append(f"Content search failed: {e}")
                results['error_count'] += 1
            
            # Test 4: Streaming behavior
            try:
                # Test that we can get an iterator
                file_iter = vexy_glob.find("*", root=str(test_root))
                first_file = next(file_iter, None)
                if first_file is not None:
                    results['streaming'] = True
                else:
                    results['errors'].append("Streaming returned no results")
            except Exception as e:
                results['errors'].append(f"Streaming test failed: {e}")
                results['error_count'] += 1
        
        finally:
            if test_root and test_root.exists():
                try:
                    shutil.rmtree(test_root)
                except:
                    pass
        
        # Calculate success rate
        total_tests = 4
        passed_tests = sum([
            results['basic_file_finding'],
            results['pattern_matching'], 
            results['content_search'],
            results['streaming']
        ])
        results['success_rate'] = passed_tests / total_tests * 100
        
        return results
    
    def run_platform_specific_tests(self) -> Dict[str, Any]:
        """Run platform-specific tests"""
        print(f"🔧 Running {self.current_platform}-specific tests...")
        
        results = {
            'platform': self.current_platform,
            'available': False,
            'test_results': None,
            'error': None
        }
        
        # Import and run platform-specific tests
        if self.current_platform == 'Windows':
            results.update(self._run_windows_tests())
        elif self.current_platform == 'Darwin':
            results.update(self._run_macos_tests())
        elif self.current_platform == 'Linux':
            results.update(self._run_linux_tests())
        else:
            results['error'] = f"Unsupported platform: {self.current_platform}"
        
        return results
    
    def _run_windows_tests(self) -> Dict[str, Any]:
        """Run Windows-specific tests"""
        test_script = Path(__file__).parent / "windows_ecosystem_test.py"
        if not test_script.exists():
            return {'available': False, 'error': 'Windows test script not found'}
        
        try:
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True, timeout=600)
            
            return {
                'available': True,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'available': True, 'error': 'Windows tests timed out (>10 minutes)'}
        except Exception as e:
            return {'available': True, 'error': f'Windows tests failed: {e}'}
    
    def _run_macos_tests(self) -> Dict[str, Any]:
        """Run macOS-specific tests"""
        test_script = Path(__file__).parent / "macos_integration_test.py"
        if not test_script.exists():
            return {'available': False, 'error': 'macOS test script not found'}
        
        try:
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True, timeout=600)
            
            return {
                'available': True,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'available': True, 'error': 'macOS tests timed out (>10 minutes)'}
        except Exception as e:
            return {'available': True, 'error': f'macOS tests failed: {e}'}
    
    def _run_linux_tests(self) -> Dict[str, Any]:
        """Run Linux-specific tests"""
        test_script = Path(__file__).parent / "linux_distro_test.py"
        if not test_script.exists():
            return {'available': False, 'error': 'Linux test script not found'}
        
        try:
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True, timeout=600)
            
            return {
                'available': True,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'available': True, 'error': 'Linux tests timed out (>10 minutes)'}
        except Exception as e:
            return {'available': True, 'error': f'Linux tests failed: {e}'}
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run cross-platform performance benchmarks"""
        print("🔧 Running performance benchmarks...")
        
        import tempfile
        import shutil
        
        results = {
            'small_dataset': {},
            'medium_dataset': {},
            'large_dataset': {},
            'error_count': 0,
            'errors': []
        }
        
        datasets = [
            ('small', 100),
            ('medium', 1000), 
            ('large', 5000)
        ]
        
        for dataset_name, num_files in datasets:
            test_root = None
            try:
                print(f"  Benchmarking {dataset_name} dataset ({num_files} files)...")
                
                # Create test dataset
                test_root = Path(tempfile.mkdtemp(prefix=f"vexy_glob_perf_{dataset_name}_"))
                
                for i in range(num_files):
                    subdir = test_root / f"dir_{i // 100}"
                    subdir.mkdir(exist_ok=True)
                    
                    filename = f"file_{i}.txt"
                    (subdir / filename).write_text(f"Content of file {i}")
                
                # Benchmark file finding
                start_time = time.perf_counter()
                files = list(vexy_glob.find("*.txt", root=str(test_root)))
                find_time = time.perf_counter() - start_time
                
                # Benchmark content search
                start_time = time.perf_counter()
                search_results = list(vexy_glob.search("Content", "*.txt", str(test_root)))
                search_time = time.perf_counter() - start_time
                
                results[f'{dataset_name}_dataset'] = {
                    'files_created': num_files,
                    'files_found': len(files),
                    'find_time': find_time,
                    'find_rate': len(files) / find_time if find_time > 0 else 0,
                    'search_results': len(search_results),
                    'search_time': search_time,
                    'search_rate': len(search_results) / search_time if search_time > 0 else 0
                }
                
                print(f"    Found {len(files)} files in {find_time:.3f}s ({len(files)/find_time:.0f} files/s)")
                print(f"    Search found {len(search_results)} matches in {search_time:.3f}s")
                
            except Exception as e:
                results['errors'].append(f"{dataset_name} benchmark failed: {e}")
                results['error_count'] += 1
            
            finally:
                if test_root and test_root.exists():
                    try:
                        shutil.rmtree(test_root)
                    except:
                        pass
        
        return results
    
    def generate_report(self, env_info: Dict, basic_results: Dict, platform_results: Dict, perf_results: Dict) -> str:
        """Generate comprehensive test report"""
        report_lines = [
            "🚀 vexy_glob Platform Compatibility Report",
            "=" * 60,
            "",
            "📋 Environment Information:",
            f"  Platform: {env_info['platform']} {env_info['platform_release']}",
            f"  Machine: {env_info['machine']}",
            f"  Python: {env_info['python_version']} ({env_info['python_implementation']})",
            f"  vexy_glob: {env_info['vexy_glob_version']}",
            ""
        ]
        
        # Add platform-specific details
        if 'linux_distro' in env_info:
            report_lines.append(f"  Linux Distribution: {env_info['linux_distro']} {env_info.get('linux_version', '')}")
        elif 'macos_version' in env_info:
            report_lines.append(f"  macOS Version: {env_info['macos_version'][0]}")
        elif 'windows_version' in env_info:
            report_lines.append(f"  Windows Version: {env_info['windows_version']}")
        
        # Basic functionality results
        report_lines.extend([
            "",
            "🔧 Basic Functionality Tests:",
            f"  Success Rate: {basic_results['success_rate']:.1f}%",
            f"  File Finding: {'✅' if basic_results['basic_file_finding'] else '❌'}",
            f"  Pattern Matching: {'✅' if basic_results['pattern_matching'] else '❌'}",
            f"  Content Search: {'✅' if basic_results['content_search'] else '❌'}",
            f"  Streaming: {'✅' if basic_results['streaming'] else '❌'}",
        ])
        
        if basic_results['errors']:
            report_lines.extend([
                "  Errors:",
                *[f"    - {error}" for error in basic_results['errors']]
            ])
        
        # Platform-specific results
        report_lines.extend([
            "",
            f"🏗️ {platform_results['platform']}-Specific Tests:",
        ])
        
        if not platform_results['available']:
            report_lines.append(f"  ❌ Platform tests not available: {platform_results.get('error', 'Unknown')}")
        elif platform_results.get('success'):
            report_lines.append("  ✅ Platform tests passed")
        else:
            report_lines.append("  ❌ Platform tests failed")
            if platform_results.get('error'):
                report_lines.append(f"    Error: {platform_results['error']}")
        
        # Performance results
        report_lines.extend([
            "",
            "🚀 Performance Benchmarks:",
        ])
        
        for dataset_name in ['small', 'medium', 'large']:
            dataset_key = f'{dataset_name}_dataset'
            if dataset_key in perf_results and 'find_rate' in perf_results[dataset_key]:
                data = perf_results[dataset_key]
                report_lines.append(
                    f"  {dataset_name.title()} ({data['files_created']} files): "
                    f"{data['find_rate']:.0f} files/s, "
                    f"{data['search_rate']:.0f} searches/s"
                )
        
        if perf_results['errors']:
            report_lines.extend([
                "  Performance Errors:",
                *[f"    - {error}" for error in perf_results['errors']]
            ])
        
        # Overall assessment
        total_time = time.time() - self.start_time
        report_lines.extend([
            "",
            "🎯 Overall Assessment:",
            f"  Test Duration: {total_time:.1f} seconds",
        ])
        
        # Calculate overall score
        basic_score = basic_results['success_rate']
        platform_score = 100 if platform_results.get('success') else 0
        perf_score = 100 if perf_results['error_count'] == 0 else 50
        
        overall_score = (basic_score + platform_score + perf_score) / 3
        
        if overall_score >= 90:
            assessment = "✅ EXCELLENT - Ready for production"
        elif overall_score >= 75:
            assessment = "🟡 GOOD - Minor issues to address"
        elif overall_score >= 50:
            assessment = "⚠️ FAIR - Several issues need attention"
        else:
            assessment = "❌ POOR - Major issues require fixing"
        
        report_lines.extend([
            f"  Overall Score: {overall_score:.1f}%",
            f"  Status: {assessment}",
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def save_detailed_results(self, results: Dict[str, Any], output_path: Path):
        """Save detailed results to JSON file"""
        results['timestamp'] = time.time()
        results['test_duration'] = time.time() - self.start_time
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: {output_path}")
    
    def run_all_tests(self, save_results: bool = True) -> bool:
        """Run all platform tests and generate report"""
        print("🚀 Starting comprehensive platform testing for vexy_glob")
        print("=" * 60)
        
        # Detect environment
        env_info = self.detect_environment()
        print(f"Environment: {env_info['platform']} {env_info['machine']}")
        print(f"Python: {env_info['python_version']}")
        print(f"vexy_glob: {env_info['vexy_glob_version']}")
        print()
        
        # Run tests
        basic_results = self.run_basic_functionality_tests()
        platform_results = self.run_platform_specific_tests()
        perf_results = self.run_performance_benchmarks()
        
        # Generate and display report
        report = self.generate_report(env_info, basic_results, platform_results, perf_results)
        print("\n" + report)
        
        # Save detailed results if requested
        if save_results:
            timestamp = int(time.time())
            output_file = Path(f"platform_test_results_{env_info['platform'].lower()}_{timestamp}.json")
            
            detailed_results = {
                'environment': env_info,
                'basic_tests': basic_results,
                'platform_tests': platform_results,
                'performance_tests': perf_results
            }
            
            self.save_detailed_results(detailed_results, output_file)
        
        # Return success status
        basic_success = basic_results['success_rate'] >= 75
        platform_success = platform_results.get('success', False) or not platform_results['available']
        perf_success = perf_results['error_count'] == 0
        
        return basic_success and platform_success and perf_success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run vexy_glob platform compatibility tests")
    parser.add_argument('--no-save', action='store_true', 
                       help="Don't save detailed results to JSON file")
    parser.add_argument('--basic-only', action='store_true',
                       help="Run only basic functionality tests")
    parser.add_argument('--platform-only', action='store_true', 
                       help="Run only platform-specific tests")
    parser.add_argument('--perf-only', action='store_true',
                       help="Run only performance benchmarks")
    
    args = parser.parse_args()
    
    coordinator = PlatformTestCoordinator()
    
    if args.basic_only:
        results = coordinator.run_basic_functionality_tests()
        print(f"Basic tests success rate: {results['success_rate']:.1f}%")
        return results['success_rate'] >= 75
    
    elif args.platform_only:
        results = coordinator.run_platform_specific_tests()
        success = results.get('success', False)
        print(f"Platform tests: {'PASSED' if success else 'FAILED'}")
        return success
    
    elif args.perf_only:
        results = coordinator.run_performance_benchmarks()
        success = results['error_count'] == 0
        print(f"Performance tests: {'PASSED' if success else 'FAILED'}")
        return success
    
    else:
        # Run all tests
        success = coordinator.run_all_tests(save_results=not args.no_save)
        return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)