"""Code analysis tools for CLine MCP Server - Java/Spring Boot focused."""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Provides code analysis capabilities with focus on Java and Spring Boot projects."""
    
    def __init__(self):
        """Initialize the CodeAnalyzer."""
        self.supported_extensions = {'.java', '.xml', '.yml', '.yaml', '.properties', '.py', '.js', '.ts'}
        self.java_keywords = {
            'public', 'private', 'protected', 'static', 'final', 'abstract', 'class', 'interface',
            'extends', 'implements', 'import', 'package', 'void', 'int', 'String', 'boolean', 'List'
        }
        self.spring_annotations = {
            '@RestController', '@Controller', '@Service', '@Repository', '@Component', '@Autowired',
            '@RequestMapping', '@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping',
            '@RequestBody', '@PathVariable', '@RequestParam', '@ResponseBody', '@EnableAutoConfiguration',
            '@SpringBootApplication', '@Configuration', '@Bean', '@Value', '@Profile'
        }
    
    async def analyze(self, path: str, analysis_type: str = "all") -> Dict[str, Any]:
        """
        Analyze code structure, dependencies, or quality for Java/Spring Boot projects.
        
        Args:
            path: Path to file or directory to analyze
            analysis_type: Type of analysis ("structure", "dependencies", "quality", "all")
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return {"error": f"Path does not exist: {path}"}
            
            results = {}
            
            if path_obj.is_file():
                if analysis_type in ["structure", "all"]:
                    results["structure"] = await self._analyze_file_structure(path_obj)
                if analysis_type in ["dependencies", "all"]:
                    results["dependencies"] = await self._analyze_file_dependencies(path_obj)
                if analysis_type in ["quality", "all"]:
                    results["quality"] = await self._analyze_code_quality(path_obj)
            else:
                if analysis_type in ["structure", "all"]:
                    results["structure"] = await self._analyze_directory_structure(path_obj)
                if analysis_type in ["dependencies", "all"]:
                    results["dependencies"] = await self._analyze_spring_boot_dependencies(path_obj)
                if analysis_type in ["quality", "all"]:
                    results["quality"] = await self._analyze_directory_quality(path_obj)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing {path}: {str(e)}")
            return {"error": str(e)}
    
    async def get_function_signatures(self, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract method signatures from a Java file.
        
        Args:
            file_path: Path to the file
            language: Programming language (auto-detected if not provided)
        
        Returns:
            Dictionary containing method signatures and metadata
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            if not language:
                language = self._detect_language(path_obj)
            
            if language == "java":
                return await self._extract_java_signatures(path_obj)
            else:
                return {"error": f"Language {language} not yet supported for signature extraction"}
                
        except Exception as e:
            logger.error(f"Error extracting signatures from {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_file_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze structure of a single file (Java focused)."""
        language = self._detect_language(file_path)
        
        if language == "java":
            return await self._analyze_java_structure(file_path)
        elif language in ["xml", "yml", "yaml", "properties"]:
            return await self._analyze_config_structure(file_path)
        else:
            return {
                "language": language,
                "classes": [],
                "methods": [],
                "imports": [],
                "lines_of_code": self._count_lines(file_path)
            }
    
    async def _analyze_java_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Java file structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            structure = {
                "language": "java",
                "package": self._extract_package(content),
                "imports": self._extract_imports(content),
                "classes": [],
                "interfaces": [],
                "methods": [],
                "annotations": [],
                "lines_of_code": self._count_lines(file_path),
                "spring_components": []
            }
            
            # Extract classes and interfaces
            classes = self._extract_classes(content)
            structure["classes"] = classes
            
            # Extract Spring annotations
            spring_annotations = self._extract_spring_annotations(content)
            structure["annotations"] = spring_annotations
            structure["spring_components"] = self._identify_spring_components(classes, spring_annotations)
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing Java structure: {str(e)}")
            return {"error": str(e)}
    
    def _extract_package(self, content: str) -> str:
        """Extract package declaration from Java file."""
        match = re.search(r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;', content)
        return match.group(1) if match else ""
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Java file."""
        imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_.*]*)\s*;', content)
        return imports
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract classes and their methods from Java file."""
        classes = []
        
        # Find class declarations
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            extends = match.group(2)
            implements = match.group(3).split(',') if match.group(3) else []
            
            # Find methods in this class
            class_content = self._extract_class_content(content, class_name)
            methods = self._extract_java_methods(class_content)
            
            class_info = {
                "name": class_name,
                "extends": extends,
                "implements": [imp.strip() for imp in implements],
                "methods": methods,
                "annotations": self._extract_class_annotations(content, class_name)
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_class_content(self, content: str, class_name: str) -> str:
        """Extract content between class braces."""
        # Find class start
        class_start = re.search(rf'(?:abstract\s+|final\s+)?class\s+{class_name}\s*{{', content)
        if not class_start:
            return ""
        
        start_pos = class_start.end()
        brace_count = 1
        current_pos = start_pos
        
        while current_pos < len(content) and brace_count > 0:
            if content[current_pos] == '{':
                brace_count += 1
            elif content[current_pos] == '}':
                brace_count -= 1
            current_pos += 1
        
        return content[start_pos:current_pos-1]
    
    def _extract_java_methods(self, class_content: str) -> List[Dict[str, Any]]:
        """Extract methods from Java class content."""
        methods = []
        
        # Method pattern (simplified)
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+|final\s+|abstract\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)(?:\s*throws\s+([^{]+))?'
        
        for match in re.finditer(method_pattern, class_content):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)
            throws = match.group(4)
            
            # Parse parameters
            parameters = []
            if params.strip():
                param_list = [p.strip() for p in params.split(',')]
                for param in param_list:
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = ' '.join(parts[:-1])
                            param_name = parts[-1]
                            parameters.append({"type": param_type, "name": param_name})
            
            methods.append({
                "name": method_name,
                "return_type": return_type,
                "parameters": parameters,
                "throws": [t.strip() for t in throws.split(',')] if throws else []
            })
        
        return methods
    
    def _extract_spring_annotations(self, content: str) -> List[str]:
        """Extract Spring annotations from Java file."""
        annotations = []
        
        for annotation in self.spring_annotations:
            if annotation in content:
                annotations.append(annotation)
        
        return annotations
    
    def _extract_class_annotations(self, content: str, class_name: str) -> List[str]:
        """Extract annotations for a specific class."""
        # Find class declaration with preceding annotations
        pattern = rf'(@[^\s]+(?:\([^)]*\))?\s*)*(?:abstract\s+|final\s+)?class\s+{class_name}'
        match = re.search(pattern, content)
        
        if match:
            annotation_text = match.group(1) or ""
            annotations = re.findall(r'@([^\s(]+)', annotation_text)
            return annotations
        
        return []
    
    def _identify_spring_components(self, classes: List[Dict[str, Any]], annotations: List[str]) -> List[Dict[str, Any]]:
        """Identify Spring components among classes."""
        components = []
        
        component_annotations = {
            '@RestController': 'Controller',
            '@Controller': 'Controller',
            '@Service': 'Service',
            '@Repository': 'Repository',
            '@Component': 'Component'
        }
        
        for class_info in classes:
            for annotation in class_info['annotations']:
                if annotation in component_annotations:
                    components.append({
                        "class": class_info['name'],
                        "type": component_annotations[annotation],
                        "annotations": class_info['annotations'],
                        "methods": [m for m in class_info['methods'] if any(req in m['name'] for req in ['get', 'post', 'put', 'delete'])]
                    })
        
        return components
    
    async def _analyze_config_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze configuration files (XML, YAML, properties)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            suffix = file_path.suffix.lower()
            structure = {
                "language": suffix[1:],  # Remove the dot
                "lines_of_code": self._count_lines(file_path),
                "config_type": "spring_config"
            }
            
            if suffix == '.xml':
                structure['spring_beans'] = self._extract_xml_beans(content)
            elif suffix in ['.yml', '.yaml']:
                structure['spring_config'] = self._extract_yaml_config(content)
            elif suffix == '.properties':
                structure['spring_properties'] = self._extract_properties(content)
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing config structure: {str(e)}")
            return {"error": str(e)}
    
    def _extract_xml_beans(self, content: str) -> List[Dict[str, Any]]:
        """Extract Spring beans from XML configuration."""
        beans = []
        bean_pattern = r'<bean\s+id="([^"]+)"\s+class="([^"]+)"[^>]*>'
        
        for match in re.finditer(bean_pattern, content):
            beans.append({
                "id": match.group(1),
                "class": match.group(2)
            })
        
        return beans
    
    def _extract_yaml_config(self, content: str) -> Dict[str, Any]:
        """Extract configuration from YAML file."""
        config = {}
        lines = content.split('\n')
        
        for line in lines:
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                config[key.strip()] = value.strip()
        
        return config
    
    def _extract_properties(self, content: str) -> Dict[str, Any]:
        """Extract properties from .properties file."""
        properties = {}
        lines = content.split('\n')
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
        
        return properties
    
    async def _analyze_spring_boot_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Analyze Spring Boot project dependencies."""
        dependencies = {
            "maven_dependencies": [],
            "gradle_dependencies": [],
            "spring_boot_starter": [],
            "database": {},
            "other_frameworks": []
        }
        
        # Check for Maven pom.xml
        pom_path = project_path / "pom.xml"
        if pom_path.exists():
            dependencies["maven_dependencies"] = await self._parse_maven_dependencies(pom_path)
        
        # Check for Gradle build.gradle
        gradle_path = project_path / "build.gradle"
        if gradle_path.exists():
            dependencies["gradle_dependencies"] = await self._parse_gradle_dependencies(gradle_path)
        
        # Identify Spring Boot starters
        all_deps = dependencies["maven_dependencies"] + dependencies["gradle_dependencies"]
        dependencies["spring_boot_starter"] = [dep for dep in all_deps if "spring-boot-starter" in dep]
        
        # Identify database dependencies
        db_keywords = ['jdbc', 'mysql', 'postgresql', 'mongodb', 'hibernate', 'jpa']
        dependencies["database"] = {
            "dependencies": [dep for dep in all_deps if any(keyword in dep.lower() for keyword in db_keywords)]
        }
        
        return dependencies
    
    async def _parse_maven_dependencies(self, pom_path: Path) -> List[str]:
        """Parse Maven dependencies from pom.xml."""
        try:
            with open(pom_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract dependency artifacts
            dependency_pattern = r'<artifactId>([^<]+-spring-boot-starter-[^<]+|[^<]+)</artifactId>'
            dependencies = re.findall(dependency_pattern, content)
            
            # Also extract full dependency info
            full_dep_pattern = r'<dependency>.*?<groupId>([^<]+)</groupId>.*?<artifactId>([^<]+)</artifactId>.*?</dependency>'
            full_deps = re.findall(full_dep_pattern, content, re.DOTALL)
            
            return [f"{group}:{artifact}" for group, artifact in full_deps]
            
        except Exception as e:
            logger.error(f"Error parsing Maven dependencies: {str(e)}")
            return []
    
    async def _parse_gradle_dependencies(self, gradle_path: Path) -> List[str]:
        """Parse Gradle dependencies from build.gradle."""
        try:
            with open(gradle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract dependency declarations
            dep_pattern = r'(?:implementation|compile|runtime)\s+\'([^\']+)\''
            dependencies = re.findall(dep_pattern, content)
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error parsing Gradle dependencies: {str(e)}")
            return []
    
    async def _analyze_code_quality(self, file_path: Path) -> Dict[str, Any]:
        """Analyze code quality metrics for Java files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            total_lines = len(lines)
            non_empty_lines = len([line for line in lines if line.strip()])
            
            # Basic quality metrics
            quality_metrics = {
                "total_lines": total_lines,
                "non_empty_lines": non_empty_lines,
                "code_ratio": non_empty_lines / total_lines if total_lines > 0 else 0,
                "max_line_length": max(len(line) for line in lines) if lines else 0,
                "long_lines": len([line for line in lines if len(line) > 120])
            }
            
            language = self._detect_language(file_path)
            if language == "java":
                quality_metrics.update(self._analyze_java_quality(content))
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing code quality: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_java_quality(self, content: str) -> Dict[str, Any]:
        """Analyze Java-specific quality metrics."""
        try:
            # Count various Java elements
            class_count = len(re.findall(r'\bclass\s+\w+', content))
            method_count = len(re.findall(r'\b(public|private|protected)\s+(static\s+)?(?:\w+<[^>]+>|\w+)\s+\w+\s*\(', content))
            
            # Count Spring annotations
            annotation_count = len(re.findall(r'@[A-Za-z]+', content))
            spring_annotation_count = len([ann for ann in self.spring_annotations if ann in content])
            
            return {
                "class_count": class_count,
                "method_count": method_count,
                "annotation_count": annotation_count,
                "spring_annotation_count": spring_annotation_count,
                "spring_ratio": spring_annotation_count / annotation_count if annotation_count > 0 else 0
            }
            
        except Exception:
            return {"java_metrics": "unavailable"}
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        
        language_map = {
            '.java': 'java',
            '.xml': 'xml',
            '.yml': 'yml',
            '.yaml': 'yaml',
            '.properties': 'properties',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript'
        }
        
        return language_map.get(suffix, 'unknown')
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception:
            return 0
    
    async def _analyze_directory_structure(self, dir_path: Path) -> Dict[str, Any]:
        """Analyze structure of a Java/Spring Boot directory."""
        files_by_type = {}
        total_files = 0
        total_lines = 0
        
        # Look for Spring Boot specific structure
        spring_structure = {
            "has_main_class": False,
            "has_application_properties": False,
            "has_test_directory": False,
            "controller_packages": [],
            "service_packages": [],
            "repository_packages": []
        }
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.supported_extensions:
                total_files += 1
                ext = file_path.suffix
                if ext not in files_by_type:
                    files_by_type[ext] = 0
                files_by_type[ext] += 1
                total_lines += self._count_lines(file_path)
                
                # Check for Spring Boot structure
                if file_path.suffix == '.java':
                    await self._check_spring_structure(file_path, spring_structure)
                elif file_path.name in ['application.properties', 'application.yml']:
                    spring_structure["has_application_properties"] = True
        
        # Check for test directory
        test_dir = dir_path / "src" / "test"
        if test_dir.exists():
            spring_structure["has_test_directory"] = True
        
        return {
            "total_files": total_files,
            "files_by_type": files_by_type,
            "total_lines_of_code": total_lines,
            "spring_boot_structure": spring_structure
        }
    
    async def _check_spring_structure(self, java_file: Path, spring_structure: Dict[str, Any]):
        """Check if Java file contains Spring Boot structure elements."""
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for main class
            if '@SpringBootApplication' in content or 'SpringApplication.run' in content:
                spring_structure["has_main_class"] = True
            
            # Check for controllers, services, repositories
            if '@RestController' in content or '@Controller' in content:
                package = self._extract_package(content)
                if package and package not in spring_structure["controller_packages"]:
                    spring_structure["controller_packages"].append(package)
            
            if '@Service' in content:
                package = self._extract_package(content)
                if package and package not in spring_structure["service_packages"]:
                    spring_structure["service_packages"].append(package)
            
            if '@Repository' in content:
                package = self._extract_package(content)
                if package and package not in spring_structure["repository_packages"]:
                    spring_structure["repository_packages"].append(package)
                    
        except Exception:
            pass
    
    async def _analyze_directory_quality(self, dir_path: Path) -> Dict[str, Any]:
        """Analyze code quality for an entire directory."""
        quality_summary = {
            "total_files": 0,
            "total_lines": 0,
            "avg_lines_per_file": 0,
            "language_breakdown": {},
            "spring_specific": {
                "total_controllers": 0,
                "total_services": 0,
                "total_repositories": 0,
                "total_config_classes": 0
            }
        }
        
        all_qualities = []
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.supported_extensions:
                quality = await self._analyze_code_quality(file_path)
                if 'error' not in quality:
                    all_qualities.append(quality)
                    quality_summary["total_files"] += 1
                    quality_summary["total_lines"] += quality.get("total_lines", 0)
                    
                    language = self._detect_language(file_path)
                    if language not in quality_summary["language_breakdown"]:
                        quality_summary["language_breakdown"][language] = {"files": 0, "lines": 0}
                    quality_summary["language_breakdown"][language]["files"] += 1
                    quality_summary["language_breakdown"][language]["lines"] += quality.get("total_lines", 0)
                    
                    # Spring-specific quality metrics
                    if language == "java":
                        spring_annotations = quality.get("spring_annotation_count", 0)
                        if "@Controller" in str(file_path) or "@RestController" in str(file_path):
                            quality_summary["spring_specific"]["total_controllers"] += 1
                        elif "@Service" in str(file_path):
                            quality_summary["spring_specific"]["total_services"] += 1
                        elif "@Repository" in str(file_path):
                            quality_summary["spring_specific"]["total_repositories"] += 1
                        elif "@Configuration" in str(file_path):
                            quality_summary["spring_specific"]["total_config_classes"] += 1
        
        if quality_summary["total_files"] > 0:
            quality_summary["avg_lines_per_file"] = quality_summary["total_lines"] / quality_summary["total_files"]
        
        return quality_summary
    

    async def _analyze_file_dependencies(self, file_path: Path) -> Dict[str, Any]:
        """Analyze dependencies of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {
                "file": str(file_path),
                "imports": [],
                "external_dependencies": [],
                "spring_dependencies": [],
                "internal_dependencies": []
            }
            
            # Extract imports
            imports = self._extract_imports(content)
            dependencies["imports"] = imports
            
            # Categorize dependencies
            for imp in imports:
                if "org.springframework" in imp:
                    dependencies["spring_dependencies"].append(imp)
                elif "java." in imp or "javax." in imp:
                    dependencies["external_dependencies"].append(imp)
                else:
                    dependencies["internal_dependencies"].append(imp)
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing file dependencies: {str(e)}")
            return {"error": str(e)}


    async def _extract_java_signatures(self, file_path: Path) -> Dict[str, Any]:
        """Extract method signatures from Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            signatures = {
                "file": str(file_path),
                "language": "java",
                "package": self._extract_package(content),
                "imports": self._extract_imports(content),
                "classes": []
            }
            
            # Extract classes and their methods
            classes = self._extract_classes(content)
            for class_info in classes:
                signatures["classes"].append({
                    "name": class_info["name"],
                    "annotations": class_info["annotations"],
                    "methods": class_info["methods"],
                    "extends": class_info.get("extends"),
                    "implements": class_info.get("implements", [])
                })
            
            return signatures
            
        except Exception as e:
            logger.error(f"Error extracting Java signatures: {str(e)}")
            return {"error": str(e)}
