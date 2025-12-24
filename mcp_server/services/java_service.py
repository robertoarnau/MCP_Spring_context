"""Service for Java and Spring Boot specific analysis."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp_server.core.interfaces import FileSystemInterface

class JavaService:
    """Handles Java and Spring Boot specific logic."""
    
    def __init__(self, fs: FileSystemInterface):
        self._fs = fs
        self.java_source_extensions = {'.java', '.xml', '.yml', '.yaml', '.properties'}
        self.springboot_directories = {
            'src/main/java', 'src/main/resources', 'src/test/java', 
            'src/test/resources', 'target', 'build', '.gradle', '.m2'
        }
        self.spring_annotations = [
            '@RestController', '@Controller', '@Service', '@Repository', 
            '@Component', '@Autowired', '@RequestMapping', '@GetMapping', 
            '@PostMapping', '@SpringBootApplication', '@Configuration'
        ]

    async def analyze_java_file(self, content: str) -> Dict[str, Any]:
        """Analyze basic Java file structure."""
        analysis = {
            "has_package": 'package' in content,
            "has_imports": 'import' in content,
            "class_count": content.count('class '),
            "interface_count": content.count('interface '),
            "method_count": content.count('public ') + content.count('private ') + content.count('protected '),
            "spring_annotations": []
        }
        
        for annotation in self.spring_annotations:
            if annotation in content:
                analysis["spring_annotations"].append(annotation)
        
        return analysis

    async def analyze_config_file(self, content: str, file_type: str) -> Dict[str, Any]:
        """Analyze configuration file content."""
        analysis = {
            "file_type": file_type,
            "lines": len(content.split('\n')),
            "key_count": 0,
            "spring_properties": []
        }
        
        if file_type in ['.yml', '.yaml']:
            lines = content.split('\n')
            analysis["key_count"] = len([line for line in lines if ':' in line and not line.strip().startswith('#')])
            spring_keys = ['spring', 'server', 'datasource', 'jpa']
            analysis["spring_properties"] = [
                line.strip() for line in lines 
                if any(key in line.lower() for key in spring_keys) and ':' in line
            ]
        elif file_type == '.properties':
            lines = content.split('\n')
            analysis["key_count"] = len([line for line in lines if '=' in line and not line.strip().startswith('#')])
            spring_keys = ['spring', 'server', 'datasource', 'jpa']
            analysis["spring_properties"] = [
                line.strip() for line in lines 
                if any(key in line.lower() for key in spring_keys) and '=' in line
            ]
        elif file_type == '.xml':
            analysis["tag_count"] = content.count('<')
            analysis["spring_beans"] = content.count('<bean')
        
        return analysis

    async def analyze_spring_structure(self, root: Path) -> Dict[str, Any]:
        """Analyze Spring Boot project structure."""
        structure = {
            "is_spring_boot_project": False,
            "has_maven": await self._fs.exists(root / "pom.xml"),
            "has_gradle": await self._fs.exists(root / "build.gradle"),
            "has_main_sources": await self._fs.exists(root / "src/main/java"),
            "has_test_sources": await self._fs.exists(root / "src/test/java"),
            "has_resources": await self._fs.exists(root / "src/main/resources"),
            "main_class": await self.get_main_class(root)
        }
        structure["is_spring_boot_project"] = structure["has_maven"] or structure["has_gradle"]
        return structure

    async def is_spring_boot_project(self, root: Path) -> bool:
        """Check if a project is a Spring Boot project."""
        return await self._fs.exists(root / "pom.xml") or await self._fs.exists(root / "build.gradle")

    async def get_main_class(self, root: Path) -> Optional[str]:
        """Find the main class with @SpringBootApplication."""
        java_dir = root / "src" / "main" / "java"
        if not await self._fs.exists(java_dir):
            return None
            
        for java_file in await self._fs.list_dir(java_dir, "*.java", recursive=True):
            content = await self._fs.read_file(java_file)
            if '@SpringBootApplication' in content or 'SpringApplication.run' in content:
                return str(java_file.relative_to(java_dir).with_suffix(''))
        return None

    def validate_java_syntax(self, content: str) -> Dict[str, Any]:
        """Basic Java syntax validation."""
        errors = []
        
        # Brace matching
        if content.count('{') != content.count('}'):
            errors.append("Mismatched braces")
        
        # Parentheses matching
        if content.count('(') != content.count(')'):
            errors.append("Mismatched parentheses")
            
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
