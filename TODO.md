# TODO.md - vexy_glob Implementation Tasks

## 🚀 CURRENT PRIORITIES - Path to v2.0.0

### Priority 1: Performance Optimization & Profiling

- [ ] **1.1 Remaining Profiling Tasks**
  - [ ] Set up Linux perf tools integration for system-level profiling

- [x] **1.4 Critical Performance Issues** ✅ **COMPLETED - ALL RESOLVED**
  - **Status**: All critical performance issues resolved, ready for v2.0.0 release

### Priority 2: Comprehensive Platform Testing & Validation

- [ ] **2.1 Windows Ecosystem Comprehensive Testing**
  - Test UNC paths (\\server\share\folder) with network drives and SharePoint mounts
  - Verify Windows drive letters (C:\, D:\, mapped network drives) and path normalization
  - Test case-insensitive NTFS behavior with mixed-case file/directory names
  - Validate Windows reserved filenames (CON, PRN, AUX, COM1-COM9, LPT1-LPT9)
  - Test NTFS junction points, hard links, and symbolic links (requires elevation)
  - Verify Windows file attributes (hidden, system, readonly) and ACL permissions
  - Test with PowerShell 5.1, PowerShell 7, cmd.exe, and Windows Terminal
  - Validate WSL1/WSL2 integration and cross-filesystem operations
  - Test with Windows Defender real-time scanning and exclusions

- [ ] **2.2 Linux Distribution Matrix Validation**
  - **Core Distributions**: Ubuntu 20.04/22.04 LTS, RHEL 8/9, Debian 11/12, Alpine 3.18+
  - **Filesystem Testing**: ext4, btrfs (subvolumes), xfs, zfs, tmpfs, and network mounts
  - **Character Encoding**: UTF-8, ISO-8859-1, GB2312, and locale-specific encodings
  - **Special Filesystems**: /proc, /sys, /dev, /tmp with proper permission handling
  - **Container Testing**: Docker, Podman, LXC with volume mounts and overlay filesystems
  - **Package Manager Integration**: Test installation via pip, conda, and system packages
  - **SELinux/AppArmor**: Validate behavior under mandatory access control systems

- [ ] **2.3 macOS Platform Integration Testing**
  - **Filesystem Features**: APFS (case-sensitive/insensitive), HFS+, and external drives
  - **macOS Metadata**: .DS_Store, .fseventsd, .Spotlight-V100, .Trashes handling
  - **Extended Attributes**: Test xattr preservation and com.apple.* attribute handling
  - **Resource Forks**: Validate legacy resource fork detection and proper skipping
  - **System Integration**: Time Machine exclusions, Spotlight indexing interference
  - **Security**: Test with System Integrity Protection (SIP) and Gatekeeper
  - **Versions**: macOS 11 (Big Sur) through macOS 14 (Sonoma) compatibility

- [ ] **2.4 Large-Scale Real-World Performance Validation**
  - **Massive Codebases**: Linux kernel (~70K files), Chromium (~300K files), LLVM (~50K files)
  - **Competitive Benchmarking**: Direct comparison with `fd` and `ripgrep` on identical datasets
  - **Stress Testing**: 1M+ file directories with deep nesting (>20 levels)
  - **Memory Profiling**: Valgrind, heaptrack analysis under extreme loads (10M+ files)
  - **Signal Handling**: SIGINT, SIGTERM graceful shutdown with resource cleanup
  - **Resource Limits**: Test ulimit scenarios (open files, memory, CPU time)
  - **Network Filesystems**: NFS, SMB/CIFS, sshfs performance characteristics

### Priority 3: Production Release Engineering (v2.0.0)

- [ ] **3.1 Pre-Release Quality Assurance**
  - **CI/CD Validation**: Execute full matrix testing (Python 3.8-3.12 × Linux/macOS/Windows)
  - **Clean Environment Testing**: Manual validation on fresh VMs (Ubuntu 22.04, Windows 11, macOS Ventura)
  - **Installation Verification**: Test pip install from wheels without development dependencies
  - **Documentation Validation**: Execute every code example in README.md and verify output
  - **Performance Regression**: Automated benchmarking against v1.0.7 baseline with acceptable thresholds
  - **Security Audit**: Run cargo audit, bandit (Python), and dependency vulnerability scanning
  - **Code Coverage**: Maintain >95% test coverage with coverage.py and tarpaulin

- [ ] **3.2 Release Engineering & Version Management**
  - **Semantic Versioning**: Update to 2.0.0 (breaking changes in performance characteristics)
  - **Version Synchronization**: Run sync_version.py to align Cargo.toml with git tags
  - **Release Notes**: Generate comprehensive changelog with performance benchmarks
  - **Wheel Building**: Build manylinux_2_17 (x86_64), macOS (Intel/ARM universal), Windows (x64)
  - **Source Distribution**: Create sdist with complete build instructions and vendored deps
  - **Test PyPI Staging**: Upload release candidate and validate installation across platforms

- [ ] **3.3 Production Launch & Distribution**
  - **PyPI Release**: Publish stable 2.0.0 with all platform wheels and comprehensive metadata
  - **GitHub Release**: Create tagged release with artifacts, changelog, and migration guide
  - **Documentation Updates**: Update shields.io badges, version numbers, and compatibility matrix
  - **Community Announcement**: Coordinate releases across Python Weekly, Hacker News, Reddit r/Python
  - **Professional Networks**: Share on LinkedIn, Twitter/X with performance benchmarks

- [ ] **3.4 Post-Release Operations & Monitoring**
  - **Analytics Setup**: Monitor PyPI download stats, GitHub star/fork growth
  - **Issue Management**: Deploy issue templates (bug-report.yml, feature-request.yml)
  - **Maintenance Planning**: Establish Dependabot schedule, security update process
  - **Community Building**: Create CONTRIBUTING.md, CODE_OF_CONDUCT.md, maintainer guidelines
  - **Roadmap Planning**: Analyze user feedback for v3.0.0 features (async support, watch mode)
  - **Performance Monitoring**: Set up continuous benchmarking in CI for regression detection

## Notes

- Build system has been modernized to use maturin directly instead of hatch
- Version management now uses git tags with setuptools-scm
