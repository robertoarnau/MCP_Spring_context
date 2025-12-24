"""Documentation tools for CLine MCP Server - Java/Spring Boot focused."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Documentation:
    """Provides documentation generation capabilities with focus on Java/Spring Boot projects."""
    
    def __init__(self):
        """Initialize the Documentation generator."""
        self.java_doc_patterns = {
            'class_doc': r'/\*\*\s*\n(.*?)\s*\*/\s*(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)',
            'method_doc': r'/\*\*\s*\n(.*?)\s*\*/\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(',
            'field_doc': r'/\*\*\s*\n(.*?)\s*\*/\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=|;)'
        }
        self.spring_endpoints = [
            '@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping', 
            '@RequestMapping', '@PatchMapping'
        ]
    
    async def generate_docs(self, target: str, format: str = "markdown") -> Dict[str, Any]:
        """
        Generate documentation for code or project.
        
        Args:
            target: File or directory to document
            format: Output format ("markdown", "html", "json")
        
        Returns:
            Dictionary containing generated documentation
        """
        try:
            target_path = Path(target)
            if not target_path.exists():
                return {"error": f"Target does not exist: {target}"}
            
            if target_path.is_file():
                return await self._generate_file_documentation(target_path, format)
            else:
                return await self._generate_project_documentation(target_path, format)
                
        except Exception as e:
            logger.error(f"Error generating documentation for {target}: {str(e)}")
            return {"error": str(e)}
    
    async def extract_comments(self, file_path: str, include_docstrings: bool = True) -> Dict[str, Any]:
        """
        Extract comments and docstrings from Java code.
        
        Args:
            file_path: Path to Java file
            include_docstrings: Whether to include Javadoc comments
        
        Returns:
            Dictionary containing extracted comments and documentation
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            if not path_obj.suffix == '.java':
                return {"error": f"File is not a Java file: {file_path}"}
            
            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                "file": str(path_obj),
                "total_lines": len(content.split('\n')),
                "comments": [],
                "javadoc": {},
                "spring_endpoints": []
            }
            
            # Extract single-line comments
            single_line_comments = re.findall(r'//(.*)', content)
            for i, comment in enumerate(single_line_comments):
                result["comments"].append({
                    "type": "single_line",
                    "content": comment.strip(),
                    "line": self._find_line_number(content, f"//{comment}")
                })
            
            # Extract multi-line comments
            multi_line_comments = re.findall(r'/\*(.*?)\*/', content, re.DOTALL)
            for comment in multi_line_comments:
                lines = [line.strip() for line in comment.split('\n') if line.strip()]
                result["comments"].append({
                    "type": "multi_line",
                    "content": lines,
                    "lines_count": len(lines)
                })
            
            if include_docstrings:
                result["javadoc"] = await self._extract_javadoc(content)
            
            # Extract Spring REST endpoints documentation
            result["spring_endpoints"] = await self._extract_spring_endpoints(content)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting comments from {file_path}: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_file_documentation(self, file_path: Path, format: str) -> Dict[str, Any]:
        """Generate documentation for a single Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyze the file
            package_match = re.search(r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;', content)
            package_name = package_match.group(1) if package_match else "default"
            
            imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_.*]*)\s*;', content)
            
            # Extract class information
            class_info = await self._extract_class_info(content)
            
            # Extract method information
            methods = await self._extract_methods_info(content)
            
            # Extract Spring-specific information
            spring_info = await self._extract_spring_info(content)
            
            documentation = {
                "file": str(file_path),
                "package": package_name,
                "imports": imports,
                "class_info": class_info,
                "methods": methods,
                "spring_info": spring_info,
                "generated_at": datetime.now().isoformat()
            }
            
            # Format output
            if format == "markdown":
                documentation["formatted"] = await self._format_as_markdown(documentation)
            elif format == "html":
                documentation["formatted"] = await self._format_as_html(documentation)
            
            return documentation
            
        except Exception as e:
            logger.error(f"Error generating file documentation: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_project_documentation(self, project_path: Path, format: str) -> Dict[str, Any]:
        """Generate documentation for an entire Spring Boot project."""
        try:
            documentation = {
                "project_name": project_path.name,
                "project_path": str(project_path),
                "generated_at": datetime.now().isoformat(),
                "structure": await self._analyze_project_structure(project_path),
                "configuration": await self._analyze_configuration(project_path),
                "controllers": await self._analyze_controllers(project_path),
                "services": await self._analyze_services(project_path),
                "repositories": await self._analyze_repositories(project_path),
                "entities": await self._analyze_entities(project_path),
                "api_documentation": await self._generate_api_docs(project_path)
            }
            
            # Format output
            if format == "markdown":
                documentation["formatted"] = await self._format_project_as_markdown(documentation)
            elif format == "html":
                documentation["formatted"] = await self._format_project_as_html(documentation)
            
            return documentation
            
        except Exception as e:
            logger.error(f"Error generating project documentation: {str(e)}")
            return {"error": str(e)}
    
    async def _extract_javadoc(self, content: str) -> Dict[str, Any]:
        """Extract Javadoc comments from Java content."""
        javadoc = {
            "class_documentation": [],
            "method_documentation": [],
            "field_documentation": []
        }
        
        # Extract class Javadoc
        class_docs = re.findall(r'/\*\*\s*\n(.*?)\s*\*/\s*(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)', content, re.DOTALL)
        for doc, class_name in class_docs:
            javadoc["class_documentation"].append({
                "class": class_name,
                "documentation": self._clean_javadoc(doc),
                "parameters": self._extract_javadoc_params(doc),
                "returns": self._extract_javadoc_return(doc),
                "throws": self._extract_javadoc_throws(doc)
            })
        
        # Extract method Javadoc
        method_docs = re.findall(r'/\*\*\s*\n(.*?)\s*\*/\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(', content, re.DOTALL)
        for doc, return_type, method_name in method_docs:
            javadoc["method_documentation"].append({
                "method": method_name,
                "return_type": return_type,
                "documentation": self._clean_javadoc(doc),
                "parameters": self._extract_javadoc_params(doc),
                "returns": self._extract_javadoc_return(doc),
                "throws": self._extract_javadoc_throws(doc)
            })
        
        return javadoc
    
    def _clean_javadoc(self, doc: str) -> str:
        """Clean Javadoc content by removing comment markers and extra whitespace."""
        lines = doc.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading * and whitespace
            line = re.sub(r'^\s*\*\s?', '', line)
            if line.strip():
                cleaned_lines.append(line.strip())
        
        return ' '.join(cleaned_lines)
    
    def _extract_javadoc_params(self, doc: str) -> List[str]:
        """Extract @param tags from Javadoc."""
        params = re.findall(r'@param\s+(\w+)\s+(.*)', doc)
        return [{"name": name, "description": desc.strip()} for name, desc in params]
    
    def _extract_javadoc_return(self, doc: str) -> Optional[str]:
        """Extract @return tag from Javadoc."""
        return_match = re.search(r'@return\s+(.*)', doc)
        return return_match.group(1).strip() if return_match else None
    
    def _extract_javadoc_throws(self, doc: str) -> List[str]:
        """Extract @throws tags from Javadoc."""
        throws = re.findall(r'@throws\s+(\w+)\s+(.*)', doc)
        return [{"exception": name, "description": desc.strip()} for name, desc in throws]
    
    async def _extract_spring_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Extract Spring REST endpoint information."""
        endpoints = []
        
        # Find methods with REST annotations
        endpoint_pattern = r'(@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping|PatchMapping)\([^{]*?\))\s*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(endpoint_pattern, content, re.DOTALL):
            annotation = match.group(1)
            return_type = match.group(2)
            method_name = match.group(3)
            
            # Extract path from annotation
            path_match = re.search(r'["\']([^"\']+)["\']', annotation)
            path = path_match.group(1) if path_match else ""
            
            # Extract HTTP method
            http_method = "GET"
            if "@PostMapping" in annotation:
                http_method = "POST"
            elif "@PutMapping" in annotation:
                http_method = "PUT"
            elif "@DeleteMapping" in annotation:
                http_method = "DELETE"
            elif "@PatchMapping" in annotation:
                http_method = "PATCH"
            elif "@RequestMapping" in annotation:
                # Extract method from RequestMapping
                method_match = re.search(r'method\s*=\s*[^{]*?["\']([^"\']+)["\']', annotation)
                http_method = method_match.group(1).upper() if method_match else "GET"
            
            endpoints.append({
                "http_method": http_method,
                "path": path,
                "method_name": method_name,
                "return_type": return_type,
                "annotation": annotation.strip()
            })
        
        return endpoints
    
    def _find_line_number(self, content: str, search_text: str) -> int:
        """Find the line number of a given text in content."""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0
    
    async def _extract_class_info(self, content: str) -> Dict[str, Any]:
        """Extract class information from Java content."""
        class_info = {
            "name": "",
            "type": "class",
            "extends": [],
            "implements": [],
            "annotations": [],
            "fields": [],
            "constructors": []
        }
        
        # Find class declaration
        class_pattern = r'(?:@([^\s]+)\s*)*(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?(class|interface|enum)\s+(\w+)(?:\s+extends\s+(\w+(?:<[^>]+>)?))?(?:\s+implements\s+([^{]+))?'
        
        match = re.search(class_pattern, content)
        if match:
            annotations = re.findall(r'@([^\s]+)', match.group(0))
            class_info["annotations"] = annotations
            class_info["type"] = match.group(2)
            class_info["name"] = match.group(3)
            
            if match.group(4):
                class_info["extends"] = [match.group(4)]
            
            if match.group(5):
                class_info["implements"] = [imp.strip() for imp in match.group(5).split(',')]
        
        # Extract fields
        field_pattern = r'(?:@([^\s]+)\s*)*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=|;)'
        
        for field_match in re.finditer(field_pattern, content):
            field_annotations = re.findall(r'@([^\s]+)', field_match.group(0))
            class_info["fields"].append({
                "type": field_match.group(2),
                "name": field_match.group(3),
                "annotations": field_annotations
            })
        
        return class_info
    
    async def _extract_methods_info(self, content: str) -> List[Dict[str, Any]]:
        """Extract method information from Java content."""
        methods = []
        
        method_pattern = r'(?:@([^\s\(\)]+)\s*)*(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(?:synchronized\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)(?:\s*throws\s+([^{]+))?'
        
        for match in re.finditer(method_pattern, content):
            annotations = re.findall(r'@([^\s\(\)]+)', match.group(0))
            return_type = match.group(2)
            method_name = match.group(3)
            params = match.group(4).strip()
            throws = match.group(5)
            
            # Parse parameters
            parameters = []
            if params:
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
                "annotations": annotations,
                "parameters": parameters,
                "throws": [t.strip() for t in throws.split(',')] if throws else []
            })
        
        return methods
    
    async def _extract_spring_info(self, content: str) -> Dict[str, Any]:
        """Extract Spring-specific information from Java content."""
        spring_info = {
            "is_spring_component": False,
            "component_type": None,
            "annotations": [],
            "endpoints": []
        }
        
        # Check for Spring annotations
        spring_annotations = [
            '@RestController', '@Controller', '@Service', '@Repository', 
            '@Component', '@Autowired', '@RequestMapping', '@Configuration'
        ]
        
        for annotation in spring_annotations:
            if annotation in content:
                spring_info["annotations"].append(annotation)
                spring_info["is_spring_component"] = True
                
                # Determine component type
                if annotation in ['@RestController', '@Controller']:
                    spring_info["component_type"] = "Controller"
                elif annotation == '@Service':
                    spring_info["component_type"] = "Service"
                elif annotation == '@Repository':
                    spring_info["component_type"] = "Repository"
                elif annotation == '@Component':
                    spring_info["component_type"] = "Component"
                elif annotation == '@Configuration':
                    spring_info["component_type"] = "Configuration"
        
        # Extract endpoints
        spring_info["endpoints"] = await self._extract_spring_endpoints(content)
        
        return spring_info
    
    async def _analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze Spring Boot project structure."""
        structure = {
            "is_maven": (project_path / "pom.xml").exists(),
            "is_gradle": (project_path / "build.gradle").exists(),
            "has_main_class": False,
            "packages": [],
            "total_java_files": 0,
            "total_test_files": 0
        }
        
        # Count Java files
        structure["total_java_files"] = len(list(project_path.rglob("*.java")))
        structure["total_test_files"] = len(list(project_path.rglob("**/test/**/*.java")))
        
        # Find main class
        for java_file in project_path.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if '@SpringBootApplication' in content or 'SpringApplication.run' in content:
                    structure["has_main_class"] = True
                    break
            except Exception:
                continue
        
        return structure
    
    async def _analyze_configuration(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project configuration files."""
        config = {
            "application_properties": {},
            "application_yml": {},
            "maven_dependencies": [],
            "gradle_dependencies": []
        }
        
        # Read application.properties
        app_props = project_path / "src" / "main" / "resources" / "application.properties"
        if app_props.exists():
            try:
                with open(app_props, 'r', encoding='utf-8') as f:
                    content = f.read()
                for line in content.split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        config["application_properties"][key.strip()] = value.strip()
            except Exception:
                pass
        
        # Read application.yml
        app_yml = project_path / "src" / "main" / "resources" / "application.yml"
        if app_yml.exists():
            try:
                with open(app_yml, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Basic YAML parsing
                for line in content.split('\n'):
                    if ':' in line and not line.strip().startswith('#'):
                        key, value = line.split(':', 1)
                        config["application_yml"][key.strip()] = value.strip()
            except Exception:
                pass
        
        return config
    
    async def _analyze_controllers(self, project_path: Path) -> List[Dict[str, Any]]:
        """Analyze all controller classes in the project."""
        controllers = []
        
        for java_file in project_path.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '@RestController' in content or '@Controller' in content:
                    controller_info = await self._extract_class_info(content)
                    controller_info["file"] = str(java_file)
                    controller_info["endpoints"] = await self._extract_spring_endpoints(content)
                    controllers.append(controller_info)
            except Exception:
                continue
        
        return controllers
    
    async def _analyze_services(self, project_path: Path) -> List[Dict[str, Any]]:
        """Analyze all service classes in the project."""
        services = []
        
        for java_file in project_path.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '@Service' in content:
                    service_info = await self._extract_class_info(content)
                    service_info["file"] = str(java_file)
                    services.append(service_info)
            except Exception:
                continue
        
        return services
    
    async def _analyze_repositories(self, project_path: Path) -> List[Dict[str, Any]]:
        """Analyze all repository classes in the project."""
        repositories = []
        
        for java_file in project_path.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '@Repository' in content:
                    repository_info = await self._extract_class_info(content)
                    repository_info["file"] = str(java_file)
                    repositories.append(repository_info)
            except Exception:
                continue
        
        return repositories
    
    async def _analyze_entities(self, project_path: Path) -> List[Dict[str, Any]]:
        """Analyze all entity classes in the project."""
        entities = []
        
        for java_file in project_path.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '@Entity' in content or '@Table' in content:
                    entity_info = await self._extract_class_info(content)
                    entity_info["file"] = str(java_file)
                    entities.append(entity_info)
            except Exception:
                continue
        
        return entities
    
    async def _generate_api_docs(self, project_path: Path) -> List[Dict[str, Any]]:
        """Generate API documentation from all controllers."""
        api_docs = []
        controllers = await self._analyze_controllers(project_path)
        
        for controller in controllers:
            for endpoint in controller.get("endpoints", []):
                api_docs.append({
                    "controller": controller.get("name"),
                    "http_method": endpoint["http_method"],
                    "path": endpoint["path"],
                    "method_name": endpoint["method_name"],
                    "return_type": endpoint["return_type"]
                })
        
        return api_docs
    
    async def _format_as_markdown(self, doc: Dict[str, Any]) -> str:
        """Format file documentation as Markdown."""
        lines = []
        lines.append(f"# {doc['class_info']['name']}")
        lines.append("")
        
        if doc['class_info']['annotations']:
            lines.append("## Annotations")
            for annotation in doc['class_info']['annotations']:
                lines.append(f"- `{annotation}`")
            lines.append("")
        
        lines.append(f"**Package:** `{doc['package']}`")
        lines.append("")
        
        if doc['spring_info']['is_spring_component']:
            lines.append(f"**Spring Component:** {doc['spring_info']['component_type']}")
            lines.append("")
        
        if doc['class_info']['extends']:
            lines.append("## Extends")
            for ext in doc['class_info']['extends']:
                lines.append(f"- {ext}")
            lines.append("")
        
        if doc['class_info']['implements']:
            lines.append("## Implements")
            for impl in doc['class_info']['implements']:
                lines.append(f"- {impl}")
            lines.append("")
        
        if doc['methods']:
            lines.append("## Methods")
            for method in doc['methods']:
                params = ", ".join([f"{p['type']} {p['name']}" for p in method['parameters']])
                lines.append(f"### {method['return_type']} {method['name']}({params})")
                
                if method['annotations']:
                    for ann in method['annotations']:
                        lines.append(f"  - `{ann}`")
                
                if method['throws']:
                    lines.append("**Throws:**")
                    for exc in method['throws']:
                        lines.append(f"  - {exc}")
                lines.append("")
        
        return "\n".join(lines)
    
    async def _format_project_as_markdown(self, doc: Dict[str, Any]) -> str:
        """Format project documentation as Markdown."""
        lines = []
        lines.append(f"# {doc['project_name']} API Documentation")
        lines.append("")
        lines.append(f"*Generated on {doc['generated_at']}*")
        lines.append("")
        
        # Project Overview
        lines.append("## Project Overview")
        lines.append(f"- Maven Project: {doc['structure']['is_maven']}")
        lines.append(f"- Gradle Project: {doc['structure']['is_gradle']}")
        lines.append(f"- Total Java Files: {doc['structure']['total_java_files']}")
        lines.append(f"- Total Test Files: {doc['structure']['total_test_files']}")
        lines.append("")
        
        # API Endpoints
        if doc['api_documentation']:
            lines.append("## API Endpoints")
            for endpoint in doc['api_documentation']:
                lines.append(f"### {endpoint['http_method']} {endpoint['path']}")
                lines.append(f"**Controller:** {endpoint['controller']}")
                lines.append(f"**Method:** {endpoint['method_name']}")
                lines.append(f"**Return Type:** {endpoint['return_type']}")
                lines.append("")
        
        return "\n".join(lines)
    
    async def _format_as_html(self, doc: Dict[str, Any]) -> str:
        """Format documentation as HTML (simplified implementation)."""
        # This would be a more complex HTML formatter
        # For now, return a basic HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Documentation for {doc.get('class_info', {}).get('name', doc.get('project_name', 'Unknown'))}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .annotation {{ background-color: #f0f0f0; padding: 2px 6px; border-radius: 3px; }}
                .method {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }}
            </style>
        </head>
        <body>
            <h1>{doc.get('class_info', {}).get('name', doc.get('project_name', 'Unknown'))}</h1>
            <p><em>Generated on {doc.get('generated_at', 'Unknown')}</em></p>
            <div class="content">
                <p>HTML formatting would be implemented here...</p>
            </div>
        </body>
        </html>
        """
        return html.strip()
