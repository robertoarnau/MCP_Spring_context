"""Unit tests for CodeAnalyzer class."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools.code_analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test cases for CodeAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a CodeAnalyzer instance for testing."""
        return CodeAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_file_structure_java(self, analyzer, sample_java_file):
        """Test analyzing Java file structure."""
        result = await analyzer.analyze(str(sample_java_file), "structure")
        
        assert "structure" in result
        assert result["structure"]["language"] == "java"
        assert result["structure"]["package"] == "com.example.demo"
        assert "DemoApplication" in [cls["name"] for cls in result["structure"]["classes"]]
        assert len(result["structure"]["classes"]) > 0
        
        # Check Spring annotations
        assert "@SpringBootApplication" in result["structure"]["annotations"]
        assert "@RestController" in result["structure"]["annotations"]

    @pytest.mark.asyncio
    async def test_analyze_file_dependencies(self, analyzer, sample_java_file):
        """Test analyzing Java file dependencies."""
        result = await analyzer.analyze(str(sample_java_file), "dependencies")
        
        assert "dependencies" in result
        assert len(result["dependencies"]["imports"]) > 0
        assert len(result["dependencies"]["spring_dependencies"]) > 0
        assert any("springframework" in dep for dep in result["dependencies"]["spring_dependencies"])

    @pytest.mark.asyncio
    async def test_analyze_code_quality(self, analyzer, sample_java_file):
        """Test analyzing code quality metrics."""
        result = await analyzer.analyze(str(sample_java_file), "quality")
        
        assert "quality" in result
        assert result["quality"]["total_lines"] > 0
        assert result["quality"]["non_empty_lines"] > 0
        assert result["quality"]["code_ratio"] > 0
        assert result["quality"]["class_count"] > 0
        assert result["quality"]["method_count"] > 0

    @pytest.mark.asyncio
    async def test_analyze_all_types(self, analyzer, sample_java_file):
        """Test analyzing all types (structure, dependencies, quality)."""
        result = await analyzer.analyze(str(sample_java_file), "all")
        
        assert "structure" in result
        assert "dependencies" in result
        assert "quality" in result

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, analyzer):
        """Test analyzing a non-existent file."""
        result = await analyzer.analyze("nonexistent.java", "all")
        
        assert "error" in result
        assert "Path does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_get_function_signatures_java(self, analyzer, sample_java_file):
        """Test extracting Java function signatures."""
        result = await analyzer.get_function_signatures(str(sample_java_file))
        
        assert "classes" in result
        assert result["language"] == "java"
        assert result["package"] == "com.example.demo"
        
        # Check that methods were extracted
        classes = result["classes"]
        assert len(classes) > 0
        
        demo_class = next(cls for cls in classes if cls["name"] == "DemoApplication")
        assert len(demo_class["methods"]) > 0
        
        # Check for main method
        main_method = next((m for m in demo_class["methods"] if m["name"] == "main"), None)
        assert main_method is not None
        assert main_method["return_type"] == "void"

    @pytest.mark.asyncio
    async def test_get_function_signatures_nonexistent_file(self, analyzer):
        """Test extracting signatures from non-existent file."""
        result = await analyzer.get_function_signatures("nonexistent.java")
        
        assert "error" in result
        assert "File does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_get_function_signatures_unsupported_language(self, analyzer, temp_dir):
        """Test extracting signatures from unsupported language."""
        # Create a Python file
        py_file = temp_dir / "test.py"
        py_file.write_text("def hello():\n    return 'Hello'")
        
        result = await analyzer.get_function_signatures(str(py_file))
        
        assert "error" in result
        assert "not yet supported" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_directory_structure(self, analyzer, sample_spring_project):
        """Test analyzing Spring Boot directory structure."""
        result = await analyzer.analyze(str(sample_spring_project), "structure")
        
        assert "structure" in result
        assert result["structure"]["total_files"] > 0
        assert result["structure"]["files_by_type"].get(".java", 0) > 0
        
        # Check Spring Boot structure detection
        spring_structure = result["structure"]["spring_boot_structure"]
        assert spring_structure["has_main_class"] is True
        assert spring_structure["has_application_properties"] is True

    @pytest.mark.asyncio
    async def test_analyze_spring_boot_dependencies(self, analyzer, sample_spring_project):
        """Test analyzing Spring Boot dependencies."""
        result = await analyzer.analyze(str(sample_spring_project), "dependencies")
        
        assert "dependencies" in result
        assert len(result["dependencies"]["maven_dependencies"]) > 0
        assert len(result["dependencies"]["spring_boot_starter"]) > 0

    def test_detect_language_java(self, analyzer):
        """Test language detection for Java files."""
        assert analyzer._detect_language(Path("test.java")) == "java"
        assert analyzer._detect_language(Path("test.xml")) == "xml"
        assert analyzer._detect_language(Path("test.yml")) == "yml"
        assert analyzer._detect_language(Path("test.py")) == "python"
        assert analyzer._detect_language(Path("test.unknown")) == "unknown"

    def test_extract_package(self, analyzer):
        """Test package extraction from Java code."""
        java_code = 'package com.example.demo;\n\npublic class Test {}'
        assert analyzer._extract_package(java_code) == "com.example.demo"
        
        java_code_no_package = 'public class Test {}'
        assert analyzer._extract_package(java_code_no_package) == ""

    def test_extract_imports(self, analyzer):
        """Test import extraction from Java code."""
        java_code = '''
        import java.util.List;
        import org.springframework.boot.SpringApplication;
        
        public class Test {}
        '''
        imports = analyzer._extract_imports(java_code)
        assert "java.util.List" in imports
        assert "org.springframework.boot.SpringApplication" in imports

    def test_extract_spring_annotations(self, analyzer):
        """Test Spring annotations extraction."""
        java_code = '''
        @SpringBootApplication
        @RestController
        public class Test {
            @GetMapping("/test")
            public String test() { return ""; }
        }
        '''
        annotations = analyzer._extract_spring_annotations(java_code)
        assert "@SpringBootApplication" in annotations
        assert "@RestController" in annotations
        assert "@GetMapping" in annotations

    def test_count_lines(self, analyzer, temp_dir):
        """Test line counting functionality."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("line1\nline2\nline3\n")
        
        assert analyzer._count_lines(test_file) == 3
        
        # Test non-existent file
        assert analyzer._count_lines(temp_dir / "nonexistent.txt") == 0

    @pytest.mark.asyncio
    async def test_analyze_config_structure_xml(self, analyzer, temp_dir):
        """Test analyzing XML configuration structure."""
        xml_content = '''<?xml version="1.0"?>
        <beans>
            <bean id="testBean" class="com.example.TestBean"/>
        </beans>'''
        
        xml_file = temp_dir / "config.xml"
        xml_file.write_text(xml_content)
        
        result = await analyzer._analyze_config_structure(xml_file)
        
        assert result["language"] == "xml"
        assert result["config_type"] == "spring_config"
        assert len(result["spring_beans"]) > 0
        assert result["spring_beans"][0]["id"] == "testBean"

    @pytest.mark.asyncio
    async def test_analyze_config_structure_yaml(self, analyzer, temp_dir):
        """Test analyzing YAML configuration structure."""
        yaml_content = '''server:
  port: 8080
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/testdb
logging:
  level:
    com.example: DEBUG'''
        
        yaml_file = temp_dir / "config.yml"
        yaml_file.write_text(yaml_content)
        
        result = await analyzer._analyze_config_structure(yaml_file)
        
        assert result["language"] == "yml"
        assert "spring_config" in result
        assert "server" in result["spring_config"]

    @pytest.mark.asyncio
    async def test_analyze_config_structure_properties(self, analyzer, temp_dir):
        """Test analyzing properties configuration structure."""
        props_content = '''server.port=8080
spring.datasource.url=jdbc:mysql://localhost:3306/testdb
logging.level.com.example=DEBUG'''
        
        props_file = temp_dir / "config.properties"
        props_file.write_text(props_content)
        
        result = await analyzer._analyze_config_structure(props_file)
        
        assert result["language"] == "properties"
        assert "spring_properties" in result
        assert result["spring_properties"]["server.port"] == "8080"

    def test_identify_spring_components(self, analyzer):
        """Test Spring component identification."""
        classes = [
            {
                "name": "UserController",
                "methods": [{"name": "getUsers"}],
                "annotations": ["@RestController"]
            },
            {
                "name": "UserService", 
                "methods": [{"name": "getAllUsers"}],
                "annotations": ["@Service"]
            },
            {
                "name": "UserRepository",
                "methods": [],
                "annotations": ["@Repository"]
            }
        ]
        
        annotations = ["@RestController", "@Service", "@Repository"]
        components = analyzer._identify_spring_components(classes, annotations)
        
        assert len(components) == 3
        assert components[0]["type"] == "Controller"
        assert components[1]["type"] == "Service"
        assert components[2]["type"] == "Repository"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_file(self, analyzer, temp_dir):
        """Test error handling for invalid files."""
        # Create a file that can't be read as text
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b'\x00\x01\x02\x03')
        
        result = await analyzer.analyze(str(binary_file), "all")
        
        # Should handle the error gracefully
        assert "structure" in result or "error" in result

    @pytest.mark.asyncio
    async def test_empty_file_analysis(self, analyzer, temp_dir):
        """Test analysis of empty files."""
        empty_file = temp_dir / "empty.java"
        empty_file.write_text("")
        
        result = await analyzer.analyze(str(empty_file), "structure")
        
        assert result["structure"]["language"] == "java"
        assert result["structure"]["package"] == ""
        assert len(result["structure"]["classes"]) == 0
        assert len(result["structure"]["imports"]) == 0
