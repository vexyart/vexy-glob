#!/usr/bin/env python3
# this_file: tests/test_symlinks.py
"""
Test symlink following functionality and loop detection.
"""

import os
import tempfile
import pytest
from pathlib import Path
import vexy_glob


def test_symlink_following_disabled_by_default():
    """Test that symlinks are not followed by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create external directory outside search area
        external_dir = tmpdir_path / "external"
        external_dir.mkdir()
        (external_dir / "external_file.txt").write_text("external content")

        # Create search area
        search_dir = tmpdir_path / "search"
        search_dir.mkdir()
        (search_dir / "regular.txt").write_text("regular content")

        # Create symlink from search area to external directory
        symlink_to_external = search_dir / "link_to_external"
        symlink_to_external.symlink_to(external_dir)

        # Test with follow_symlinks=False (default)
        results = list(vexy_glob.find("*", root=search_dir, follow_symlinks=False))

        # Should include symlink itself but not traverse through it
        file_names = [Path(r).name for r in results]
        assert "regular.txt" in file_names
        assert "link_to_external" in file_names
        # Should NOT include contents from the symlinked directory
        assert "external_file.txt" not in file_names


def test_symlink_following_enabled():
    """Test that symlinks are followed when follow_symlinks=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create external directory outside search area
        external_dir = tmpdir_path / "external"
        external_dir.mkdir()
        (external_dir / "external_file.txt").write_text("external content")

        # Create search area
        search_dir = tmpdir_path / "search"
        search_dir.mkdir()
        (search_dir / "regular.txt").write_text("regular content")

        # Create symlink from search area to external directory
        symlink_to_external = search_dir / "link_to_external"
        symlink_to_external.symlink_to(external_dir)

        # Test with follow_symlinks=True
        results = list(vexy_glob.find("*", root=search_dir, follow_symlinks=True))

        # Should include symlink itself AND traverse through it
        file_names = [Path(r).name for r in results]
        assert "regular.txt" in file_names
        assert "link_to_external" in file_names
        # Should ALSO include contents from the symlinked directory
        assert "external_file.txt" in file_names


def test_symlink_loop_detection():
    """Test that symlink loops are detected and handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a directory
        dir1 = tmpdir_path / "dir1"
        dir1.mkdir()

        # Create a file in the directory
        (dir1 / "file1.txt").write_text("content1")

        # Create a symlink that creates a loop (dir1 -> dir1/link_to_parent -> dir1)
        loop_link = dir1 / "link_to_parent"
        loop_link.symlink_to(tmpdir_path)

        # Test with follow_symlinks=True - should not hang or crash
        results = list(vexy_glob.find("*.txt", root=tmpdir, follow_symlinks=True))

        # Should find the file but not get stuck in the loop
        assert len(results) >= 1
        assert any("file1.txt" in r for r in results)


def test_symlink_depth_behavior():
    """Test symlink behavior with max_depth restrictions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create external deep directory structure
        external_dir = tmpdir_path / "external"
        deep_dir = external_dir / "deep" / "nested"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep_file.txt").write_text("deep content")

        # Create search area with limited depth
        search_dir = tmpdir_path / "search"
        search_dir.mkdir()
        (search_dir / "root.txt").write_text("root")

        # Create symlink to deep external directory
        symlink_to_deep = search_dir / "deep_link"
        symlink_to_deep.symlink_to(deep_dir)

        # Test with max_depth=1 and follow_symlinks=True
        results = list(
            vexy_glob.find(
                "*.txt", root=search_dir, follow_symlinks=True, max_depth=1, file_type="f"
            )
        )

        file_names = [Path(r).name for r in results]
        assert "root.txt" in file_names
        # The deep_file.txt should be accessible through symlink despite depth limit
        # (symlinks can bypass depth restrictions in some implementations)
        # This test mainly ensures no crashes occur


def test_symlink_with_content_search():
    """Test symlink following with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a file with specific content
        target_file = tmpdir_path / "target.py"
        target_file.write_text("def my_function():\n    return 'hello'")

        # Create a symlink to the file
        symlink_file = tmpdir_path / "link.py"
        symlink_file.symlink_to(target_file)

        # Test content search without following symlinks
        results_no_follow = list(
            vexy_glob.search("my_function", "*.py", root=tmpdir, follow_symlinks=False)
        )

        # Should find content in original file only
        assert len(results_no_follow) == 1
        assert "target.py" in results_no_follow[0]["path"]

        # Test content search with following symlinks
        results_follow = list(
            vexy_glob.search("my_function", "*.py", root=tmpdir, follow_symlinks=True)
        )

        # Should find content in both original file and symlink
        # (Note: depending on implementation, might deduplicate)
        assert len(results_follow) >= 1
        paths = [r["path"] for r in results_follow]
        assert any("target.py" in p for p in paths)


def test_symlink_with_file_type_filtering():
    """Test symlink following with file type filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create target file and directory
        target_file = tmpdir_path / "target.txt"
        target_file.write_text("content")

        target_dir = tmpdir_path / "target_dir"
        target_dir.mkdir()

        # Create symlinks
        file_link = tmpdir_path / "file_link"
        dir_link = tmpdir_path / "dir_link"

        file_link.symlink_to(target_file)
        dir_link.symlink_to(target_dir)

        # Test finding only files with symlinks enabled
        file_results = list(vexy_glob.find("*", root=tmpdir, follow_symlinks=True, file_type="f"))

        # Should include both original file and file symlink
        file_names = [Path(r).name for r in file_results]
        assert "target.txt" in file_names
        assert "file_link" in file_names
        assert "target_dir" not in file_names
        assert "dir_link" not in file_names

        # Test finding only directories with symlinks enabled
        dir_results = list(vexy_glob.find("*", root=tmpdir, follow_symlinks=True, file_type="d"))

        # Should include both original directory and directory symlink
        dir_names = [Path(r).name for r in dir_results]
        assert "target_dir" in dir_names
        assert "dir_link" in dir_names
        assert "target.txt" not in dir_names
        assert "file_link" not in dir_names


def test_symlink_with_filters():
    """Test symlink following combined with other filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create target files with different sizes
        small_file = tmpdir_path / "small.txt"
        large_file = tmpdir_path / "large.txt"

        small_file.write_text("small")  # ~5 bytes
        large_file.write_text("large content here" * 10)  # ~190 bytes

        # Create symlinks
        small_link = tmpdir_path / "small_link"
        large_link = tmpdir_path / "large_link"

        small_link.symlink_to(small_file)
        large_link.symlink_to(large_file)

        # Test with size filter and symlink following
        results = list(
            vexy_glob.find(
                "*",
                root=tmpdir,
                follow_symlinks=True,
                min_size=50,  # Exclude small files
                file_type="f",
            )
        )

        file_names = [Path(r).name for r in results]
        assert "large.txt" in file_names
        assert "large_link" in file_names
        assert "small.txt" not in file_names
        assert "small_link" not in file_names


def test_broken_symlink_handling():
    """Test handling of broken symlinks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a symlink to a non-existent file
        broken_link = tmpdir_path / "broken_link"
        broken_link.symlink_to(tmpdir_path / "nonexistent.txt")

        # Create a valid file for comparison
        valid_file = tmpdir_path / "valid.txt"
        valid_file.write_text("valid content")

        # Test with follow_symlinks=False - should include broken symlink
        results_no_follow = list(vexy_glob.find("*", root=tmpdir, follow_symlinks=False))
        file_names = [Path(r).name for r in results_no_follow]
        assert "broken_link" in file_names
        assert "valid.txt" in file_names

        # Test with follow_symlinks=True - should handle broken symlink gracefully
        results_follow = list(vexy_glob.find("*", root=tmpdir, follow_symlinks=True))
        file_names = [Path(r).name for r in results_follow]
        assert "valid.txt" in file_names
        # Broken symlink behavior may vary - should not crash


def test_symlink_complex_scenario():
    """Test a complex symlink scenario with nested structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create complex directory structure
        src_dir = tmpdir_path / "src"
        lib_dir = tmpdir_path / "lib"

        src_dir.mkdir()
        lib_dir.mkdir()

        # Create files
        (src_dir / "main.py").write_text("import lib; lib.function()")
        (lib_dir / "module.py").write_text("def function(): pass")

        # Create symlinks for easier access
        lib_link = src_dir / "lib"
        lib_link.symlink_to(lib_dir)

        main_link = tmpdir_path / "main_link.py"
        main_link.symlink_to(src_dir / "main.py")

        # Test finding Python files with symlinks
        results = list(vexy_glob.find("*.py", root=tmpdir, follow_symlinks=True, file_type="f"))

        # Should find files through symlinks
        file_names = [Path(r).name for r in results]
        assert "main.py" in file_names
        assert "module.py" in file_names
        assert "main_link.py" in file_names

        # Test content search through symlinks
        content_results = list(
            vexy_glob.search("function", "*.py", root=tmpdir, follow_symlinks=True)
        )

        # Should find function definition through symlinked directory
        assert len(content_results) >= 1
        paths = [r["path"] for r in content_results]
        assert any("module.py" in p for p in paths)


def test_symlink_parameter_validation():
    """Test that symlink parameter is properly validated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a simple file
        test_file = tmpdir_path / "test.txt"
        test_file.write_text("test")

        # Test with explicit follow_symlinks=False
        results_false = list(vexy_glob.find("*", root=tmpdir, follow_symlinks=False))
        assert len(results_false) >= 1

        # Test with explicit follow_symlinks=True
        results_true = list(vexy_glob.find("*", root=tmpdir, follow_symlinks=True))
        assert len(results_true) >= 1

        # Results should be the same when no symlinks are present
        assert len(results_false) == len(results_true)
