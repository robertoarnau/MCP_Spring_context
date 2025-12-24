"""Unit tests for FileManager class."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools.file_manager import FileManager


class TestFileManager:
    """Test cases for FileManager class."""

    @pytest.fixture
    def file_manager(self):
        """Create a FileManager instance for testing with injected dependencies."""
        from mcp_server.infrastructure.filesystem import AIOFileSystem
        from mcp_server.services.java_service import JavaService
        from mcp_server.services.file_service import FileService
        
        fs = AIOFileSystem()
        java_service = JavaService(fs)
        file_service = FileService(fs, java_service)
        return FileManager(file_service, java_service)

    @pytest.mark.asyncio
    async def test_list_files_directory(self, file_manager, sample_spring_project):
        """Test listing files in a directory."""
        result = await file_manager.list_files(str(sample_spring_project))
        
        assert result["directory"] == str(sample_spring_project)
        assert result["total_files"] > 0
        assert len(result["files"]) > 0
        assert len(result["spring_boot_files"]) > 0
        
        # Check that Java files are included
        java_files = [f for f in result["files"] if f["extension"] == ".java"]
        assert len(java_files) > 0

    @pytest.mark.asyncio
    async def test_list_files_with_pattern(self, file_manager, sample_spring_project):
        """Test listing files with a specific pattern."""
        result = await file_manager.list_files(str(sample_spring_project), "*.java")
        
        assert len(result["files"]) > 0
        # All files should have .java extension
        for file in result["files"]:
            assert file["extension"] == ".java"

    @pytest.mark.asyncio
    async def test_list_files_non_recursive(self, file_manager, temp_dir):
        """Test listing files non-recursively."""
        # Create nested structure
        (temp_dir / "subdir").mkdir()
        (temp_dir / "root.txt").write_text("root")
        (temp_dir / "subdir" / "nested.txt").write_text("nested")
        
        result = await file_manager.list_files(str(temp_dir), recursive=False)
        
        # Should only find root.txt, not nested.txt
        file_names = [f["name"] for f in result["files"]]
        assert "root.txt" in file_names
        assert "nested.txt" not in file_names

    @pytest.mark.asyncio
    async def test_list_files_nonexistent_directory(self, file_manager):
        """Test listing files from non-existent directory."""
        result = await file_manager.list_files("/nonexistent/directory")
        
        assert "error" in result
        assert "Directory does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_read_file_text(self, file_manager, sample_java_file):
        """Test reading a text file."""
        result = await file_manager.read_file(str(sample_java_file))
        
        assert result["file_path"] == str(sample_java_file)
        assert "content" in result
        assert "package com.example.demo" in result["content"]
        assert "metadata" in result
        assert result["metadata"]["extension"] == ".java"
        assert result["metadata"]["is_java_file"] is True

    @pytest.mark.asyncio
    async def test_read_file_binary(self, file_manager, temp_dir):
        """Test reading a binary file."""
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b'\x00\x01\x02\x03')
        
        result = await file_manager.read_file(str(binary_file))
        
        assert "content" in result
        assert "Binary file" in result["content"]
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_read_file_with_java_analysis(self, file_manager, sample_java_file):
        """Test reading file with Java analysis."""
        result = await file_manager.read_file(str(sample_java_file), include_metadata=True)
        
        assert "java_analysis" in result
        assert result["java_analysis"]["has_package"] is True
        assert result["java_analysis"]["has_imports"] is True
        assert result["java_analysis"]["class_count"] > 0
        assert len(result["java_analysis"]["spring_annotations"]) > 0

    @pytest.mark.asyncio
    async def test_read_file_with_config_analysis(self, file_manager, sample_config_files):
        """Test reading configuration files with analysis."""
        # Test properties file
        result = await file_manager.read_file(str(sample_config_files["properties"]))
        
        assert "config_analysis" in result
        assert result["config_analysis"]["file_type"] == ".properties"
        assert result["config_analysis"]["key_count"] > 0

    @pytest.mark.asyncio
    async def test_read_file_nonexistent(self, file_manager):
        """Test reading a non-existent file."""
        result = await file_manager.read_file("/nonexistent/file.txt")
        
        assert "error" in result
        assert "File does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_create_file_new(self, file_manager, temp_dir):
        """Test creating a new file."""
        file_path = temp_dir / "new_file.java"
        content = "package test;\n\npublic class NewFile {}"
        
        result = await file_manager.create_file(str(file_path), content)
        
        assert result["success"] is True
        assert file_path.exists()
        assert file_path.read_text() == content
        assert result["metadata"]["name"] == "new_file.java"

    @pytest.mark.asyncio
    async def test_create_file_exists_no_overwrite(self, file_manager, temp_dir):
        """Test creating a file that already exists without overwrite."""
        file_path = temp_dir / "existing.txt"
        file_path.write_text("original")
        
        result = await file_manager.create_file(str(file_path), "new content", overwrite=False)
        
        assert "error" in result
        assert "already exists" in result["error"]
        assert file_path.read_text() == "original"  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_create_file_exists_overwrite(self, file_manager, temp_dir):
        """Test creating a file that already exists with overwrite."""
        file_path = temp_dir / "existing.txt"
        file_path.write_text("original")
        
        result = await file_manager.create_file(str(file_path), "new content", overwrite=True)
        
        assert result["success"] is True
        assert file_path.read_text() == "new content"

    @pytest.mark.asyncio
    async def test_create_file_with_directory_creation(self, file_manager, temp_dir):
        """Test creating a file in a non-existent directory."""
        file_path = temp_dir / "new_dir" / "subdir" / "file.txt"
        content = "test content"
        
        result = await file_manager.create_file(str(file_path), content)
        
        assert result["success"] is True
        assert file_path.exists()
        assert file_path.read_text() == content

    @pytest.mark.asyncio
    async def test_update_file(self, file_manager, temp_dir):
        """Test updating an existing file."""
        file_path = temp_dir / "update_test.txt"
        file_path.write_text("original content")
        
        new_content = "updated content"
        result = await file_manager.update_file(str(file_path), new_content)
        
        assert result["success"] is True
        assert file_path.read_text() == new_content
        
        # Check backup was created
        backup_path = temp_dir / "update_test.txt.backup"
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"

    @pytest.mark.asyncio
    async def test_update_file_nonexistent(self, file_manager, temp_dir):
        """Test updating a non-existent file."""
        result = await file_manager.update_file(str(temp_dir / "nonexistent.txt"), "content")
        
        assert "error" in result
        assert "does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_file(self, file_manager, temp_dir):
        """Test deleting a file."""
        file_path = temp_dir / "delete_test.txt"
        file_path.write_text("to be deleted")
        
        result = await file_manager.delete_file(str(file_path))
        
        assert result["success"] is True
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_file_with_backup(self, file_manager, temp_dir):
        """Test deleting a file with backup creation."""
        file_path = temp_dir / "delete_backup_test.txt"
        file_path.write_text("to be deleted")
        
        result = await file_manager.delete_file(str(file_path), create_backup=True)
        
        assert result["success"] is True
        assert not file_path.exists()
        
        # Check backup was created
        backup_dir = temp_dir / ".backup"
        backup_path = backup_dir / "delete_backup_test.txt"
        assert backup_path.exists()
        assert backup_path.read_text() == "to be deleted"

    @pytest.mark.asyncio
    async def test_delete_file_nonexistent(self, file_manager, temp_dir):
        """Test deleting a non-existent file."""
        result = await file_manager.delete_file(str(temp_dir / "nonexistent.txt"))
        
        assert "error" in result
        assert "does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_search_files(self, file_manager, sample_spring_project):
        """Test searching files for content."""
        result = await file_manager.search_files(str(sample_spring_project), "SpringBootApplication")
        
        assert result["total_matches"] > 0
        assert len(result["files_with_matches"]) > 0
        
        # Check that matches contain line numbers
        for match in result["files_with_matches"]:
            assert "matches" in match
            assert "lines" in match
            assert len(match["lines"]) > 0
            for line in match["lines"]:
                assert "line_number" in line
                assert "content" in line

    @pytest.mark.asyncio
    async def test_search_files_with_pattern(self, file_manager, sample_spring_project):
        """Test searching files with pattern filter."""
        result = await file_manager.search_files(str(sample_spring_project), "class", "*.java")
        
        assert "total_matches" in result
        assert result["file_pattern"] == "*.java"
        
        # All matched files should be Java files
        for match in result["files_with_matches"]:
            assert match["file"].endswith(".java")

    @pytest.mark.asyncio
    async def test_search_files_nonexistent_directory(self, file_manager):
        """Test searching in non-existent directory."""
        result = await file_manager.search_files("/nonexistent", "test")
        
        assert "error" in result
        assert "Directory does not exist" in result["error"]

    def test_get_file_info(self, file_manager, temp_dir):
        """Test getting file information."""
        test_file = temp_dir / "info_test.txt"
        test_file.write_text("test content")
        
        result = file_manager._get_file_info(test_file)
        
        assert result["name"] == "info_test.txt"
        assert result["extension"] == ".txt"
        assert result["size"] > 0
        assert result["is_java_file"] is False
        assert result["is_config_file"] is False
        assert "hash" in result

    def test_format_size(self, file_manager):
        """Test file size formatting."""
        assert file_manager._format_size(500) == "500.0 B"
        assert file_manager._format_size(1500) == "1.5 KB"
        assert file_manager._format_size(1500000) == "1.5 MB"
        assert file_manager._format_size(1500000000) == "1.5 GB"

    @pytest.mark.asyncio
    async def test_analyze_spring_structure(self, file_manager, sample_spring_project):
        """Test Spring Boot structure analysis."""
        structure = await file_manager._analyze_spring_structure(sample_spring_project)
        
        assert structure["has_maven"] is True
        assert structure["has_main_sources"] is True
        assert structure["has_resources"] is True
        assert structure["main_class"] is not None

    @pytest.mark.asyncio
    async def test_analyze_spring_structure_gradle(self, file_manager, temp_dir):
        """Test Spring Boot structure analysis with Gradle."""
        # Create build.gradle
        (temp_dir / "build.gradle").write_text("plugins { id 'org.springframework.boot' }")
        (temp_dir / "src" / "main" / "java").mkdir(parents=True)
        
        structure = await file_manager._analyze_spring_structure(temp_dir)
        
        assert structure["has_gradle"] is True
        assert structure["is_spring_boot_project"] is True

    @pytest.mark.asyncio
    async def test_analyze_java_file_structure(self, file_manager, temp_dir):
        """Test Java file structure analysis."""
        java_content = '''
        package com.example.demo;
        
        import org.springframework.boot.SpringApplication;
        import org.springframework.boot.autoconfigure.SpringBootApplication;
        
        @SpringBootApplication
        public class TestApp {
            public static void main(String[] args) {
                SpringApplication.run(TestApp.class, args);
            }
        }
        '''
        
        result = await file_manager._analyze_java_file_structure(java_content)
        
        assert result["has_package"] is True
        assert result["has_imports"] is True
        assert result["class_count"] == 1
        assert result["method_count"] >= 1
        assert "@SpringBootApplication" in result["spring_annotations"]

    @pytest.mark.asyncio
    async def test_analyze_config_file_properties(self, file_manager):
        """Test properties file analysis."""
        content = '''
        server.port=8080
        spring.datasource.url=jdbc:mysql://localhost:3306/testdb
        # This is a comment
        logging.level.root=INFO
        '''
        
        result = await file_manager._analyze_config_file(content, ".properties")
        
        assert result["file_type"] == ".properties"
        assert result["key_count"] == 3  # Excluding comments
        assert len(result["spring_properties"]) == 2  # server and spring properties

    @pytest.mark.asyncio
    async def test_analyze_config_file_yaml(self, file_manager):
        """Test YAML file analysis."""
        content = '''
        server:
          port: 8080
        spring:
          datasource:
            url: jdbc:mysql://localhost:3306/testdb
        # This is a comment
        logging:
          level:
            root: INFO
        '''
        
        result = await file_manager._analyze_config_file(content, ".yml")
        
        assert result["file_type"] == ".yml"
        assert result["key_count"] >= 4  # Non-comment lines with colons
        assert len(result["spring_properties"]) >= 2  # server and spring properties

    @pytest.mark.asyncio
    async def test_validate_java_syntax_valid(self, file_manager):
        """Test Java syntax validation for valid code."""
        content = '''
        public class TestClass {
            public void testMethod() {
                System.out.println("Hello");
            }
        }
        '''
        
        result = await file_manager._validate_java_syntax(content)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_java_syntax_invalid(self, file_manager):
        """Test Java syntax validation for invalid code."""
        content = '''
        public class TestClass {
            public void testMethod() {
                System.out.println("Hello"  // Missing semicolon
            }
        '''
        
        result = await file_manager._validate_java_syntax(content)
        
        assert result["valid"] is False
        # The exact validation depends on the implementation, but there should be some indication of issues
        assert len(result["errors"]) > 0 or len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_unicode_file_handling(self, file_manager, temp_dir):
        """Test handling of unicode content in files."""
        unicode_content = "package test;\n\n// Unicode test: ñáéíóú\npublic class UnicodeTest {}"
        unicode_file = temp_dir / "unicode.java"
        unicode_file.write_text(unicode_content, encoding='utf-8')
        
        result = await file_manager.read_file(str(unicode_file))
        
        assert result["content"] == unicode_content
        assert "ñáéíóú" in result["content"]

    @pytest.mark.asyncio
    async def test_large_file_handling(self, file_manager, temp_dir):
        """Test handling of large files."""
        # Create a reasonably large file
        large_content = "public class LargeFile {\n"
        large_content += "    public void method" + "{};\n".format(1) * 100
        large_content += "}\n"
        
        large_file = temp_dir / "large.java"
        large_file.write_text(large_content)
        
        result = await file_manager.read_file(str(large_file))
        
        assert result["content"] == large_content
        assert result["metadata"]["size"] > 0
