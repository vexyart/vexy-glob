// this_file: benches/datasets.rs
//! Benchmark dataset generators for comprehensive performance testing
//! 
//! This module provides realistic test environments that mirror real-world
//! usage patterns for file finding and content search operations.

use std::fs::{File, create_dir_all};
use std::io::Write;
use std::path::Path;
use tempfile::TempDir;

/// Dataset scale configurations for benchmarking
#[derive(Debug, Clone)]
pub struct DatasetConfig {
    pub name: &'static str,
    pub total_files: usize,
    pub directories: usize,
    pub max_depth: usize,
    pub file_types: Vec<&'static str>,
    pub content_patterns: Vec<&'static str>,
}

impl DatasetConfig {
    /// Small dataset for quick benchmarking (CI-friendly)
    pub fn small() -> Self {
        Self {
            name: "small",
            total_files: 1000,
            directories: 20,
            max_depth: 4,
            file_types: vec!["py", "rs", "js", "md", "txt"],
            content_patterns: vec!["TODO", "FIXME", "target_pattern"],
        }
    }

    /// Medium dataset for realistic project simulation
    pub fn medium() -> Self {
        Self {
            name: "medium",
            total_files: 10000,
            directories: 100,
            max_depth: 8,
            file_types: vec!["py", "rs", "js", "ts", "md", "json", "yaml", "toml", "txt", "c", "h", "cpp"],
            content_patterns: vec!["TODO", "FIXME", "BUG", "HACK", "NOTE", "target_pattern", "import", "function"],
        }
    }

    /// Large dataset for stress testing
    pub fn large() -> Self {
        Self {
            name: "large",
            total_files: 100000,
            directories: 1000,
            max_depth: 12,
            file_types: vec![
                "py", "rs", "js", "ts", "jsx", "tsx", "md", "json", "yaml", "toml", "txt", 
                "c", "h", "cpp", "cc", "cxx", "java", "kt", "go", "rb", "php", "cs", "sh", "sql"
            ],
            content_patterns: vec![
                "TODO", "FIXME", "BUG", "HACK", "NOTE", "WARNING", "DEPRECATED", "target_pattern",
                "import", "function", "class", "struct", "interface", "const", "let", "var"
            ],
        }
    }

    /// Real-world project structures for validation
    pub fn realistic_projects() -> Vec<ProjectTemplate> {
        vec![
            ProjectTemplate::python_web_app(),
            ProjectTemplate::rust_cli_tool(),
            ProjectTemplate::react_frontend(),
            ProjectTemplate::nodejs_backend(),
            ProjectTemplate::cpp_library(),
        ]
    }
}

/// Realistic project structure templates
#[derive(Debug, Clone)]
pub struct ProjectTemplate {
    pub name: &'static str,
    pub structure: Vec<DirectoryTemplate>,
}

#[derive(Debug, Clone)]
pub struct DirectoryTemplate {
    pub path: &'static str,
    pub files: Vec<FileTemplate>,
}

#[derive(Debug, Clone)]
pub struct FileTemplate {
    pub name: &'static str,
    pub extension: &'static str,
    pub content_template: &'static str,
    pub size_lines: usize,
}

impl ProjectTemplate {
    /// Python web application structure (Django/Flask style)
    pub fn python_web_app() -> Self {
        Self {
            name: "python_web_app",
            structure: vec![
                DirectoryTemplate {
                    path: "src",
                    files: vec![
                        FileTemplate {
                            name: "main",
                            extension: "py",
                            content_template: "from flask import Flask\napp = Flask(__name__)\n# TODO: Add routes\ndef hello():\n    return 'Hello World!'\nif __name__ == '__main__':\n    app.run(debug=True)",
                            size_lines: 50,
                        },
                        FileTemplate {
                            name: "models",
                            extension: "py", 
                            content_template: "from sqlalchemy import Column, Integer, String\nclass User:\n    # target_pattern for testing\n    id = Column(Integer, primary_key=True)\n    name = Column(String(80))",
                            size_lines: 100,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "tests",
                    files: vec![
                        FileTemplate {
                            name: "test_main",
                            extension: "py",
                            content_template: "import pytest\nfrom src.main import app\n# FIXME: Add more comprehensive tests\ndef test_hello():\n    assert True  # target_pattern",
                            size_lines: 30,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "static",
                    files: vec![
                        FileTemplate {
                            name: "style",
                            extension: "css",
                            content_template: "body { margin: 0; padding: 0; }\n.container { max-width: 1200px; }",
                            size_lines: 200,
                        },
                    ],
                },
            ],
        }
    }

    /// Rust CLI tool structure (Cargo workspace style)
    pub fn rust_cli_tool() -> Self {
        Self {
            name: "rust_cli_tool",
            structure: vec![
                DirectoryTemplate {
                    path: "src",
                    files: vec![
                        FileTemplate {
                            name: "main",
                            extension: "rs",
                            content_template: "use clap::Parser;\n// TODO: Implement CLI arguments\n#[derive(Parser)]\nstruct Args {\n    // target_pattern for search\n    file: String,\n}\nfn main() {\n    println!(\"Hello, world!\");\n}",
                            size_lines: 80,
                        },
                        FileTemplate {
                            name: "lib",
                            extension: "rs",
                            content_template: "pub mod utils;\npub mod config;\n// FIXME: Add error handling\npub fn process_file(path: &str) -> Result<(), Box<dyn std::error::Error>> {\n    // target_pattern implementation\n    Ok(())\n}",
                            size_lines: 150,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "tests",
                    files: vec![
                        FileTemplate {
                            name: "integration",
                            extension: "rs",
                            content_template: "#[test]\nfn test_basic_functionality() {\n    // NOTE: target_pattern for testing\n    assert!(true);\n}",
                            size_lines: 25,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "benches",
                    files: vec![
                        FileTemplate {
                            name: "performance",
                            extension: "rs",
                            content_template: "use criterion::{black_box, criterion_group, criterion_main, Criterion};\n// Performance benchmark with target_pattern\nfn bench_main(c: &mut Criterion) {\n    c.bench_function(\"main\", |b| b.iter(|| black_box(42)));\n}",
                            size_lines: 40,
                        },
                    ],
                },
            ],
        }
    }

    /// React frontend structure (modern JavaScript/TypeScript)
    pub fn react_frontend() -> Self {
        Self {
            name: "react_frontend",
            structure: vec![
                DirectoryTemplate {
                    path: "src/components",
                    files: vec![
                        FileTemplate {
                            name: "App",
                            extension: "tsx",
                            content_template: "import React from 'react';\n// TODO: Add proper TypeScript types\ninterface Props {\n  title: string;\n}\nconst App: React.FC<Props> = ({ title }) => {\n  // target_pattern for component\n  return <div>{title}</div>;\n};",
                            size_lines: 60,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "src/hooks",
                    files: vec![
                        FileTemplate {
                            name: "useApi",
                            extension: "ts",
                            content_template: "import { useState, useEffect } from 'react';\n// HACK: Quick implementation - needs refactoring\nexport function useApi<T>(url: string) {\n  const [data, setData] = useState<T | null>(null);\n  // target_pattern hook\n  return { data };\n}",
                            size_lines: 45,
                        },
                    ],
                },
            ],
        }
    }

    /// Node.js backend structure (Express/NestJS style)
    pub fn nodejs_backend() -> Self {
        Self {
            name: "nodejs_backend",
            structure: vec![
                DirectoryTemplate {
                    path: "src/controllers",
                    files: vec![
                        FileTemplate {
                            name: "userController",
                            extension: "js",
                            content_template: "const express = require('express');\n// NOTE: target_pattern for API endpoint\nconst getUserById = async (req, res) => {\n  // FIXME: Add proper error handling\n  try {\n    res.json({ success: true });\n  } catch (error) {\n    res.status(500).json({ error: error.message });\n  }\n};",
                            size_lines: 75,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "src/middleware",
                    files: vec![
                        FileTemplate {
                            name: "auth",
                            extension: "js",
                            content_template: "// Authentication middleware with target_pattern\nconst jwt = require('jsonwebtoken');\nmodule.exports = (req, res, next) => {\n  // TODO: Implement JWT validation\n  const token = req.headers.authorization;\n  next();\n};",
                            size_lines: 35,
                        },
                    ],
                },
            ],
        }
    }

    /// C++ library structure (CMake style)
    pub fn cpp_library() -> Self {
        Self {
            name: "cpp_library",
            structure: vec![
                DirectoryTemplate {
                    path: "include",
                    files: vec![
                        FileTemplate {
                            name: "library",
                            extension: "h",
                            content_template: "#ifndef LIBRARY_H\n#define LIBRARY_H\n// target_pattern header\nclass Library {\npublic:\n    // TODO: Add public interface\n    void process();\nprivate:\n    int m_value;\n};\n#endif",
                            size_lines: 25,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "src",
                    files: vec![
                        FileTemplate {
                            name: "library",
                            extension: "cpp",
                            content_template: "#include \"library.h\"\n#include <iostream>\n// FIXME: Implement proper algorithm\nvoid Library::process() {\n    // target_pattern implementation\n    std::cout << \"Processing...\" << std::endl;\n    // NOTE: Add error handling here\n}",
                            size_lines: 50,
                        },
                    ],
                },
                DirectoryTemplate {
                    path: "tests",
                    files: vec![
                        FileTemplate {
                            name: "test_library",
                            extension: "cpp",
                            content_template: "#include <gtest/gtest.h>\n#include \"library.h\"\n// Unit test with target_pattern\nTEST(LibraryTest, BasicFunctionality) {\n    Library lib;\n    // HACK: Simple test for now\n    EXPECT_NO_THROW(lib.process());\n}",
                            size_lines: 30,
                        },
                    ],
                },
            ],
        }
    }
}

/// Generate a comprehensive test environment with multiple dataset scales
pub fn create_comprehensive_test_environment() -> TempDir {
    let tmp_dir = TempDir::new().expect("Failed to create temp directory");
    let base_path = tmp_dir.path();

    // Create small, medium, and large datasets in subdirectories
    create_synthetic_dataset(base_path, DatasetConfig::small()).unwrap();
    create_synthetic_dataset(base_path, DatasetConfig::medium()).unwrap();
    
    // Create realistic project structures
    for project in DatasetConfig::realistic_projects() {
        create_project_structure(base_path, &project).unwrap();
    }

    // Create filesystem-specific test scenarios
    create_special_cases(base_path).unwrap();

    tmp_dir
}

/// Generate a synthetic dataset based on configuration
pub fn create_synthetic_dataset(base_path: &Path, config: DatasetConfig) -> std::io::Result<()> {
    let dataset_root = base_path.join(format!("dataset_{}", config.name));
    create_dir_all(&dataset_root)?;

    let files_per_dir = config.total_files / config.directories;
    
    for dir_i in 0..config.directories {
        let dir_path = dataset_root.join(format!("dir_{:04}", dir_i));
        create_dir_all(&dir_path)?;

        // Create nested subdirectories based on max_depth
        let mut current_path = dir_path.clone();
        for depth in 1..=config.max_depth.min(6) {
            current_path = current_path.join(format!("level_{}", depth));
            create_dir_all(&current_path)?;
        }

        // Distribute files across directory levels
        for file_i in 0..files_per_dir {
            let file_ext = config.file_types[file_i % config.file_types.len()];
            let pattern = config.content_patterns[file_i % config.content_patterns.len()];
            
            // Vary file placement across directory depths
            let depth_level = file_i % (config.max_depth + 1);
            let mut file_path = dir_path.clone();
            for d in 1..=depth_level.min(config.max_depth) {
                let level_path = file_path.join(format!("level_{}", d));
                // Ensure the directory exists before using it
                create_dir_all(&level_path).ok();
                file_path = level_path;
            }
            
            let file_name = file_path.join(format!("file_{:06}.{}", file_i, file_ext));
            let mut file = File::create(&file_name)?;
            
            // Generate realistic file content with patterns
            writeln!(file, "// File: {}", file_name.display())?;
            writeln!(file, "// Generated for {} dataset", config.name)?;
            writeln!(file, "")?;
            
            // Add content with search patterns
            for line_i in 0..20 {
                if line_i % 5 == 0 {
                    writeln!(file, "// {}: Line {} with search pattern", pattern, line_i)?;
                } else if line_i % 7 == 0 {
                    writeln!(file, "function process_{}() {{ /* {} implementation */ }}", line_i, pattern)?;
                } else {
                    writeln!(file, "let value_{} = {}; // Standard content", line_i, line_i * 42)?;
                }
            }
        }
    }

    // Create .gitignore and other metadata files
    let mut gitignore = File::create(dataset_root.join(".gitignore"))?;
    writeln!(gitignore, "*.log")?;
    writeln!(gitignore, "*.tmp")?;
    writeln!(gitignore, "build/")?;
    writeln!(gitignore, "target/")?;
    writeln!(gitignore, "__pycache__/")?;
    writeln!(gitignore, "node_modules/")?;

    Ok(())
}

/// Create realistic project structures from templates
pub fn create_project_structure(base_path: &Path, project: &ProjectTemplate) -> std::io::Result<()> {
    let project_root = base_path.join(format!("project_{}", project.name));
    create_dir_all(&project_root)?;

    for dir_template in &project.structure {
        let dir_path = project_root.join(dir_template.path);
        create_dir_all(&dir_path)?;

        for file_template in &dir_template.files {
            let file_name = format!("{}.{}", file_template.name, file_template.extension);
            let file_path = dir_path.join(&file_name);
            let mut file = File::create(&file_path)?;

            // Write base template content
            writeln!(file, "{}", file_template.content_template)?;
            
            // Add additional lines to reach target size
            for i in 0..file_template.size_lines.saturating_sub(10) {
                writeln!(file, "// Additional content line {} for realistic file size", i)?;
            }
        }
    }

    Ok(())
}

/// Create special filesystem test cases (edge cases, performance traps)
pub fn create_special_cases(base_path: &Path) -> std::io::Result<()> {
    let special_root = base_path.join("special_cases");
    create_dir_all(&special_root)?;

    // Deep directory nesting (performance test)
    let mut deep_path = special_root.join("deep_nesting");
    for i in 0..50 {
        deep_path = deep_path.join(format!("level_{:02}", i));
        create_dir_all(&deep_path)?;
        
        if i % 10 == 0 {
            let mut file = File::create(deep_path.join("marker.txt"))?;
            writeln!(file, "Deep file at level {} with target_pattern", i)?;
        }
    }

    // Many files in single directory (filesystem stress test)
    let flat_dir = special_root.join("flat_many_files");
    create_dir_all(&flat_dir)?;
    for i in 0..5000 {
        let mut file = File::create(flat_dir.join(format!("file_{:05}.txt", i)))?;
        writeln!(file, "File {} with target_pattern content", i)?;
    }

    // Mixed file sizes (small, medium, large)
    let size_test_dir = special_root.join("file_sizes");
    create_dir_all(&size_test_dir)?;
    
    // Small files (< 1KB)
    for i in 0..100 {
        let mut file = File::create(size_test_dir.join(format!("small_{}.txt", i)))?;
        writeln!(file, "Small file {} target_pattern", i)?;
    }
    
    // Medium files (~10KB)
    for i in 0..50 {
        let mut file = File::create(size_test_dir.join(format!("medium_{}.txt", i)))?;
        for line in 0..200 {
            writeln!(file, "Medium file {} line {} with target_pattern content", i, line)?;
        }
    }
    
    // Large files (~100KB)
    for i in 0..10 {
        let mut file = File::create(size_test_dir.join(format!("large_{}.txt", i)))?;
        for line in 0..2000 {
            writeln!(file, "Large file {} line {} with extensive target_pattern content and additional text to increase file size", i, line)?;
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dataset_creation() {
        let tmp_dir = TempDir::new().unwrap();
        let config = DatasetConfig::small();
        
        create_synthetic_dataset(tmp_dir.path(), config).unwrap();
        
        // Verify dataset was created
        assert!(tmp_dir.path().join("dataset_small").exists());
    }

    #[test]
    fn test_project_structure_creation() {
        let tmp_dir = TempDir::new().unwrap();
        let project = ProjectTemplate::python_web_app();
        
        create_project_structure(tmp_dir.path(), &project).unwrap();
        
        // Verify project structure was created
        assert!(tmp_dir.path().join("project_python_web_app").exists());
        assert!(tmp_dir.path().join("project_python_web_app/src/main.py").exists());
    }
    
    #[test]
    fn test_comprehensive_environment() {
        let _test_env = create_comprehensive_test_environment();
        // Just verify it doesn't panic
    }
}