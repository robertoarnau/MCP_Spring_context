"""File management tools for CLine MCP Server - Java/Spring Boot focused."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import mimetypes
import hashlib

logger = logging.getLogger(__name__)

class FileManager:
    """Provides file management capabilities with focus on Java/Spring Boot projects."""
    
    def __init__(self):
        """Initialize the FileManager."""
        self.java_source_extensions = {'.java', '.xml', '.yml', '.yaml', '.properties'}
        self.config_files = {
            'pom.xml', 'build.gradle', 'application.properties', 
            'application.yml', 'application.yaml', 'settings.gradle'
        }
        self.springboot_directories = {
            'src/main/java', 'src/main/resources', 'src/test/java', 
            'src/test/resources', 'target', 'build', '.gradle', '.m2'
        }
    
    async def list_files(self, directory: str, pattern: Optional[str] = None, recursive: bool = True) -> Dict[str, Any]:
        """
        List files in directory with filtering options.
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., *.java, *.xml)
            recursive: Whether to search recursively
        
        Returns:
            Dictionary containing file listings and metadata
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {"error": f"Directory does not exist: {directory}"}
            
            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {directory}"}
            
            files = []
            directories = []
            spring_boot_files = []
            config_files = []
            
            search_pattern = pattern if pattern else "*"
            
            if recursive:
                items = dir_path.rglob(search_pattern)
            else:
                items = dir_path.glob(search_pattern)
            
            for item in items:
                if item.is_file():
                    file_info = await self._get_file_info(item)
                    files.append(file_info)
                    
                    # Categorize files
                    if item.name in self.config_files or item.parent.name == 'resources':
                        config_files.append(file_info)
                    
                    if item.suffix in self.java_source_extensions:
                        spring_boot_files.append(file_info)
                        
                elif item.is_dir() and not recursive:
                    dir_info = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory",
                        "is_spring_dir": str(item.relative_to(dir_path)) in self.springboot_directories
                    }
                    directories.append(dir_info)
            
            return {
                "directory": str(dir_path),
                "total_files": len(files),
                "total_directories": len(directories),
                "files": files,
                "directories": directories,
                "spring_boot_files": spring_boot_files,
                "config_files": config_files,
                "spring_boot_structure": self._analyze_spring_structure(dir_path)
            }
            
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {str(e)}")
            return {"error": str(e)}
    
    async def read_file(self, file_path: str, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Read file content with metadata.
        
        Args:
            file_path: Path to file
            include_metadata: Whether to include file metadata
        
        Returns:
            Dictionary containing file content and metadata
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            if not path_obj.is_file():
                return {"error": f"Path is not a file: {file_path}"}
            
            # Read file content
            try:
                with open(path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try binary read for non-text files
                with open(path_obj, 'rb') as f:
                    content = f.read()
                content = f"<Binary file - {len(content)} bytes>"
            
            result = {
                "file_path": str(path_obj),
                "content": content
            }
            
            if include_metadata:
                result["metadata"] = await self._get_file_info(path_obj)
                
                # Add Java/Spring Boot specific analysis
                if path_obj.suffix == '.java':
                    result["java_analysis"] = await self._analyze_java_file_structure(content)
                elif path_obj.suffix in ['.xml', '.yml', '.yaml', '.properties']:
                    result["config_analysis"] = await self._analyze_config_file(content, path_obj.suffix)
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def create_file(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Create a new file with content.
        
        Args:
            file_path: Path where to create the file
            content: File content
            overwrite: Whether to overwrite existing file
        
        Returns:
            Dictionary containing operation result
        """
        try:
            path_obj = Path(file_path)
            
            # Check if file exists
            if path_obj.exists() and not overwrite:
                return {"error": f"File already exists: {file_path}"}
            
            # Create parent directories if they don't exist
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path_obj, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # For Java files, validate basic syntax
            if path_obj.suffix == '.java':
                validation = await self._validate_java_syntax(content)
                if not validation["valid"]:
                    logger.warning(f"Created Java file with potential syntax issues: {validation['errors']}")
            
            return {
                "success": True,
                "file_path": str(path_obj),
                "message": f"File created successfully: {file_path}",
                "metadata": await self._get_file_info(path_obj)
            }
            
        except Exception as e:
            logger.error(f"Error creating file {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def update_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Update an existing file with new content.
        
        Args:
            file_path: Path to the file to update
            content: New file content
        
        Returns:
            Dictionary containing operation result
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            # Create backup
            backup_path = path_obj.with_suffix(f"{path_obj.suffix}.backup")
            shutil.copy2(path_obj, backup_path)
            
            # Update file
            with open(path_obj, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": str(path_obj),
                "backup_path": str(backup_path),
                "message": f"File updated successfully: {file_path}",
                "metadata": await self._get_file_info(path_obj)
            }
            
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def delete_file(self, file_path: str, create_backup: bool = False) -> Dict[str, Any]:
        """
        Delete a file with optional backup creation.
        
        Args:
            file_path: Path to the file to delete
            create_backup: Whether to create a backup before deletion
        
        Returns:
            Dictionary containing operation result
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            backup_path = None
            if create_backup:
                backup_dir = path_obj.parent / ".backup"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / path_obj.name
                shutil.copy2(path_obj, backup_path)
            
            # Delete file
            path_obj.unlink()
            
            return {
                "success": True,
                "file_path": str(path_obj),
                "backup_path": str(backup_path) if backup_path else None,
                "message": f"File deleted successfully: {file_path}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def search_files(self, directory: str, search_term: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for files containing specific text.
        
        Args:
            directory: Directory to search in
            search_term: Text to search for
            file_pattern: File pattern to limit search (e.g., *.java)
        
        Returns:
            Dictionary containing search results
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {"error": f"Directory does not exist: {directory}"}
            
            results = []
            search_pattern = file_pattern if file_pattern else "*"
            
            for file_path in dir_path.rglob(search_pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if search_term.lower() in content.lower():
                            lines_with_matches = []
                            for i, line in enumerate(content.split('\n'), 1):
                                if search_term.lower() in line.lower():
                                    lines_with_matches.append({
                                        "line_number": i,
                                        "content": line.strip()
                                    })
                            
                            results.append({
                                "file": str(file_path),
                                "matches": len(lines_with_matches),
                                "lines": lines_with_matches
                            })
                    except UnicodeDecodeError:
                        # Skip binary files
                        continue
            
            return {
                "search_term": search_term,
                "directory": str(dir_path),
                "file_pattern": search_pattern,
                "total_matches": len(results),
                "files_with_matches": results
            }
            
        except Exception as e:
            logger.error(f"Error searching files in {directory}: {str(e)}")
            return {"error": str(e)}
    
    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive file information."""
        try:
            stat = file_path.stat()
            file_hash = await self._calculate_file_hash(file_path)
            
            return {
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "extension": file_path.suffix,
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "is_java_file": file_path.suffix == '.java',
                "is_config_file": file_path.name in self.config_files,
                "hash": file_hash
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _analyze_spring_structure(self, dir_path: Path) -> Dict[str, Any]:
        """Analyze Spring Boot project structure."""
        structure = {
            "is_spring_boot_project": False,
            "has_maven": False,
            "has_gradle": False,
            "has_main_sources": False,
            "has_test_sources": False,
            "has_resources": False,
            "package_structure": [],
            "main_class": None
        }
        
        # Check for build files
        if (dir_path / "pom.xml").exists():
            structure["has_maven"] = True
            structure["is_spring_boot_project"] = True
        
        if (dir_path / "build.gradle").exists():
            structure["has_gradle"] = True
            structure["is_spring_boot_project"] = True
        
        # Check for source directories
        if (dir_path / "src" / "main" / "java").exists():
            structure["has_main_sources"] = True
        
        if (dir_path / "src" / "test" / "java").exists():
            structure["has_test_sources"] = True
        
        if (dir_path / "src" / "main" / "resources").exists():
            structure["has_resources"] = True
        
        # Find main class
        java_dir = dir_path / "src" / "main" / "java"
        if java_dir.exists():
            for java_file in java_dir.rglob("*.java"):
                try:
                    with open(java_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if '@SpringBootApplication' in content or 'SpringApplication.run' in content:
                        structure["main_class"] = f"{java_file.relative_to(java_dir).with_suffix('')}"
                        break
                except Exception:
                    continue
        
        return structure
    
    async def _analyze_java_file_structure(self, content: str) -> Dict[str, Any]:
        """Analyze basic Java file structure."""
        analysis = {
            "has_package": 'package' in content,
            "has_imports": 'import' in content,
            "class_count": content.count('class '),
            "interface_count": content.count('interface '),
            "method_count": content.count('public ') + content.count('private ') + content.count('protected '),
            "spring_annotations": []
        }
        
        # Extract Spring annotations
        spring_annotations = [
            '@RestController', '@Controller', '@Service', '@Repository', 
            '@Component', '@Autowired', '@RequestMapping', '@GetMapping', 
            '@PostMapping', '@SpringBootApplication', '@Configuration'
        ]
        
        for annotation in spring_annotations:
            if annotation in content:
                analysis["spring_annotations"].append(annotation)
        
        return analysis
    
    async def _analyze_config_file(self, content: str, file_type: str) -> Dict[str, Any]:
        """Analyze configuration file content."""
        analysis = {
            "file_type": file_type,
            "lines": len(content.split('\n')),
            "key_count": 0,
            "spring_properties": []
        }
        
        if file_type in ['.yml', '.yaml']:
            # Count YAML keys
            lines = content.split('\n')
            analysis["key_count"] = len([line for line in lines if ':' in line and not line.strip().startswith('#')])
            
            # Look for Spring properties
            spring_keys = ['spring', 'server', 'logging', 'datasource', 'jpa']
            analysis["spring_properties"] = [
                line.strip() for line in lines 
                if any(key in line.lower() for key in spring_keys) and ':' in line
            ]
            
        elif file_type == '.properties':
            # Count properties keys
            lines = content.split('\n')
            analysis["key_count"] = len([line for line in lines if '=' in line and not line.strip().startswith('#')])
            
            # Look for Spring properties
            spring_keys = ['spring', 'server', 'logging', 'datasource', 'jpa']
            analysis["spring_properties"] = [
                line.strip() for line in lines 
                if any(key in line.lower() for key in spring_keys) and '=' in line
            ]
        
        elif file_type == '.xml':
            # Basic XML analysis
            analysis["tag_count"] = content.count('<')
            analysis["spring_beans"] = content.count('<bean')
        
        return analysis
    
    async def _validate_java_syntax(self, content: str) -> Dict[str, Any]:
        """Basic Java syntax validation."""
        errors = []
        
        # Check for matching braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
        
        # Check for matching parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            errors.append(f"Mismatched parentheses: {open_parens} open, {close_parens} close")
        
        # Check for semicolons at end of statements (basic check)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}') and not any(stripped.startswith(keyword) for keyword in ['package', 'import', '//', '/*', '*']):
                if not any(marker in stripped for marker in ['class', 'interface', '@', 'if', 'for', 'while', 'else']):
                    if '(' in stripped or ')' in stripped:
                        if not stripped.startswith('for(') and not stripped.startswith('while(') and not stripped.startswith('if('):
                            errors.append(f"Line {i}: Possible missing semicolon")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []  # Could add warnings here
        }
