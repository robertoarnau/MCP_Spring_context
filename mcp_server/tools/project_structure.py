"""Project structure analysis tools for CLine MCP Server - Java/Spring Boot focused."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import re

logger = logging.getLogger(__name__)

class ProjectStructure:
    """Provides project structure analysis capabilities with focus on Java/Spring Boot projects."""
    
    def __init__(self):
        """Initialize the ProjectStructure analyzer."""
        self.java_extensions = {'.java', '.xml', '.yml', '.yaml', '.properties', '.gradle'}
        self.spring_indicators = {
            'annotations': [
                '@SpringBootApplication', '@RestController', '@Controller', '@Service', 
                '@Repository', '@Component', '@Autowired', '@Configuration'
            ],
            'config_files': [
                'application.properties', 'application.yml', 'application.yaml',
                'pom.xml', 'build.gradle', 'settings.gradle'
            ],
            'directories': [
                'src/main/java', 'src/main/resources', 'src/test/java',
                'src/test/resources', 'target', 'build', '.gradle', '.m2'
            ]
        }
    
    async def get_structure(self, root_path: str, depth: int = 3, include_file_sizes: bool = False) -> Dict[str, Any]:
        """
        Get detailed project structure and overview.
        
        Args:
            root_path: Root directory path
            depth: Maximum depth for directory traversal
            include_file_sizes: Whether to include file sizes in analysis
        
        Returns:
            Dictionary containing project structure information
        """
        try:
            root = Path(root_path)
            if not root.exists():
                return {"error": f"Project root does not exist: {root_path}"}
            
            if not root.is_dir():
                return {"error": f"Path is not a directory: {root_path}"}
            
            structure = {
                "project_name": root.name,
                "root_path": str(root),
                "total_size": 0,
                "total_files": 0,
                "total_directories": 0,
                "file_types": {},
                "directory_tree": await self._build_directory_tree(root, depth, include_file_sizes),
                "java_analysis": await self._analyze_java_structure(root),
                "spring_boot_analysis": await self._analyze_spring_boot_structure(root),
                "build_system_analysis": await self._analyze_build_system(root)
            }
            
            # Calculate totals
            structure["total_files"] = len(list(root.rglob("*")))
            structure["total_directories"] = len([d for d in root.rglob("*") if d.is_dir()])
            
            # Analyze file types
            for file_path in root.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext not in structure["file_types"]:
                        structure["file_types"][ext] = {"count": 0, "total_size": 0}
                    structure["file_types"][ext]["count"] += 1
                    
                    if include_file_sizes:
                        try:
                            size = file_path.stat().st_size
                            structure["file_types"][ext]["total_size"] += size
                            structure["total_size"] += size
                        except Exception:
                            continue
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing project structure: {str(e)}")
            return {"error": str(e)}
    
    async def detect_technologies(self, project_path: str) -> Dict[str, Any]:
        """
        Detect technologies and frameworks used in project.
        
        Args:
            project_path: Path to project directory
        
        Returns:
            Dictionary containing detected technologies
        """
        try:
            project_root = Path(project_path)
            if not project_root.exists():
                return {"error": f"Project path does not exist: {project_path}"}
            
            technologies = {
                "java_version": await self._detect_java_version(project_root),
                "spring_boot": await self._detect_spring_boot(project_root),
                "build_system": await self._detect_build_system(project_root),
                "database": await self._detect_database(project_root),
                "testing_frameworks": await self._detect_testing_frameworks(project_root),
                "other_frameworks": await self._detect_other_frameworks(project_root),
                "dependencies": await self._get_all_dependencies(project_root)
            }
            
            return technologies
            
        except Exception as e:
            logger.error(f"Error detecting technologies: {str(e)}")
            return {"error": str(e)}
    
    async def _build_directory_tree(self, root: Path, max_depth: int, include_file_sizes: bool) -> Dict[str, Any]:
        """Build a hierarchical directory tree representation."""
        def build_tree_node(path: Path, current_depth: int) -> Dict[str, Any]:
            if current_depth > max_depth:
                return None
            
            node = {
                "name": path.name,
                "path": str(path.relative_to(root)),
                "type": "directory" if path.is_dir() else "file",
                "children": []
            }
            
            if path.is_file() and include_file_sizes:
                try:
                    node["size"] = path.stat().st_size
                except Exception:
                    node["size"] = 0
            
            if path.is_dir():
                try:
                    children = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                    for child in children:
                        child_node = build_tree_node(child, current_depth + 1)
                        if child_node:
                            node["children"].append(child_node)
                except PermissionError:
                    node["error"] = "Permission denied"
            
            return node
        
        return build_tree_node(root, 0)
    
    async def _analyze_java_structure(self, project_root: Path) -> Dict[str, Any]:
        """Analyze Java-specific structure."""
        java_analysis = {
            "total_java_files": 0,
            "packages": set(),
            "main_classes": [],
            "test_classes": [],
            "config_classes": [],
            "spring_components": {
                "controllers": [],
                "services": [],
                "repositories": [],
                "components": []
            }
        }
        
        for java_file in project_root.rglob("*.java"):
            java_analysis["total_java_files"] += 1
            
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract package
                package_match = re.search(r'package\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*;', content)
                if package_match:
                    java_analysis["packages"].add(package_match.group(1))
                
                # Check file type based on path
                if 'test' in str(java_file):
                    java_analysis["test_classes"].append(str(java_file.relative_to(project_root)))
                else:
                    java_analysis["main_classes"].append(str(java_file.relative_to(project_root)))
                
                # Check for Spring components
                if '@RestController' in content or '@Controller' in content:
                    java_analysis["spring_components"]["controllers"].append(str(java_file.relative_to(project_root)))
                elif '@Service' in content:
                    java_analysis["spring_components"]["services"].append(str(java_file.relative_to(project_root)))
                elif '@Repository' in content:
                    java_analysis["spring_components"]["repositories"].append(str(java_file.relative_to(project_root)))
                elif '@Component' in content:
                    java_analysis["spring_components"]["components"].append(str(java_file.relative_to(project_root)))
                elif '@Configuration' in content:
                    java_analysis["config_classes"].append(str(java_file.relative_to(project_root)))
                    
            except Exception:
                continue
        
        # Convert set to list for JSON serialization
        java_analysis["packages"] = list(java_analysis["packages"])
        
        return java_analysis
    
    async def _analyze_spring_boot_structure(self, project_root: Path) -> Dict[str, Any]:
        """Analyze Spring Boot specific structure."""
        spring_analysis = {
            "is_spring_boot_project": False,
            "spring_boot_version": None,
            "main_class": None,
            "application_config": {},
            "rest_endpoints": 0,
            "spring_annotations_found": []
        }
        
        # Check for Spring Boot indicators
        spring_indicators_found = 0
        
        # Check for main class
        for java_file in project_root.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '@SpringBootApplication' in content:
                    spring_analysis["is_spring_boot_project"] = True
                    spring_analysis["main_class"] = str(java_file.relative_to(project_root))
                    spring_indicators_found += 1
                    break
                    
            except Exception:
                continue
        
        # Check for application properties
        app_props = project_root / "src" / "main" / "resources" / "application.properties"
        app_yml = project_root / "src" / "main" / "resources" / "application.yml"
        
        if app_props.exists():
            spring_analysis["is_spring_boot_project"] = True
            try:
                with open(app_props, 'r', encoding='utf-8') as f:
                    content = f.read()
                spring_analysis["application_config"]["properties"] = self._parse_properties(content)
                spring_indicators_found += 1
            except Exception:
                pass
        
        if app_yml.exists():
            spring_analysis["is_spring_boot_project"] = True
            try:
                with open(app_yml, 'r', encoding='utf-8') as f:
                    content = f.read()
                spring_analysis["application_config"]["yaml"] = self._parse_yaml(content)
                spring_indicators_found += 1
            except Exception:
                pass
        
        # Count Spring annotations
        all_java_files = list(project_root.rglob("*.java"))
        for java_file in all_java_files:
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for annotation in self.spring_indicators['annotations']:
                    if annotation in content:
                        spring_analysis["spring_annotations_found"].append(annotation)
                        spring_indicators_found += 1
                
                # Count REST endpoints
                spring_analysis["rest_endpoints"] += len(re.findall(
                    r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)', content
                ))
                    
            except Exception:
                continue
        
        spring_analysis["spring_annotations_found"] = list(set(spring_analysis["spring_annotations_found"]))
        
        return spring_analysis
    
    async def _analyze_build_system(self, project_root: Path) -> Dict[str, Any]:
        """Analyze build system (Maven/Gradle)."""
        build_analysis = {
            "build_system": "unknown",
            "build_files": [],
            "dependencies": [],
            "plugins": [],
            "profiles": []
        }
        
        # Check for Maven
        pom_xml = project_root / "pom.xml"
        if pom_xml.exists():
            build_analysis["build_system"] = "maven"
            build_analysis["build_files"].append("pom.xml")
            
            try:
                tree = ET.parse(pom_xml)
                root = tree.getroot()
                
                # Extract dependencies
                deps = root.findall('.//{http://maven.apache.org/POM/4.0.0}dependency')
                for dep in deps:
                    group_id = dep.find('.//{http://maven.apache.org/POM/4.0.0}groupId')
                    artifact_id = dep.find('.//{http://maven.apache.org/POM/4.0.0}artifactId')
                    version = dep.find('.//{http://maven.apache.org/POM/4.0.0}version')
                    
                    if group_id is not None and artifact_id is not None:
                        dep_info = {
                            "group_id": group_id.text,
                            "artifact_id": artifact_id.text,
                            "version": version.text if version is not None else None
                        }
                        build_analysis["dependencies"].append(dep_info)
                
                # Extract profiles
                profiles = root.findall('.//{http://maven.apache.org/POM/4.0.0}profile')
                for profile in profiles:
                    profile_id = profile.find('.//{http://maven.apache.org/POM/4.0.0}id')
                    if profile_id is not None:
                        build_analysis["profiles"].append(profile_id.text)
                        
            except Exception as e:
                logger.error(f"Error parsing pom.xml: {str(e)}")
        
        # Check for Gradle
        build_gradle = project_root / "build.gradle"
        settings_gradle = project_root / "settings.gradle"
        
        if build_gradle.exists():
            build_analysis["build_system"] = "gradle"
            build_analysis["build_files"].append("build.gradle")
            
            try:
                with open(build_gradle, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract dependencies
                dep_pattern = r'(?:implementation|compile|runtime|testImplementation)\s+["\']([^"\']+)["\']'
                dependencies = re.findall(dep_pattern, content)
                build_analysis["dependencies"] = [{"identifier": dep} for dep in dependencies]
                
                # Extract plugins
                plugin_pattern = r'apply plugin:\s*["\']([^"\']+)["\']|plugins\s*\{[^}]*id\s+["\']([^"\']+)["\']'
                plugins = re.findall(plugin_pattern, content)
                build_analysis["plugins"] = [plugin[0] or plugin[1] for plugin in plugins]
                
            except Exception as e:
                logger.error(f"Error parsing build.gradle: {str(e)}")
        
        if settings_gradle.exists():
            build_analysis["build_files"].append("settings.gradle")
        
        return build_analysis
    
    async def _detect_java_version(self, project_root: Path) -> Dict[str, Any]:
        """Detect Java version from build files."""
        java_info = {"version": "unknown", "source": "unknown"}
        
        # Check Maven pom.xml
        pom_xml = project_root / "pom.xml"
        if pom_xml.exists():
            try:
                with open(pom_xml, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for Java version properties
                java_props = {'java.version', 'maven.compiler.source', 'maven.compiler.target'}
                for prop in java_props:
                    pattern = f'<{prop}>([^<]+)</{prop}>'
                    match = re.search(pattern, content)
                    if match:
                        java_info["version"] = match.group(1)
                        java_info["source"] = "maven"
                        break
            except Exception:
                pass
        
        # Check Gradle
        build_gradle = project_root / "build.gradle"
        if build_gradle.exists() and java_info["version"] == "unknown":
            try:
                with open(build_gradle, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for Java version
                java_patterns = [
                    r'sourceCompatibility\s*=\s*["\']?([^"\']+)["\']?',
                    r'targetCompatibility\s*=\s*["\']?([^"\']+)["\']?',
                    r'java\.version\s*=\s*["\']?([^"\']+)["\']?'
                ]
                
                for pattern in java_patterns:
                    match = re.search(pattern, content)
                    if match:
                        java_info["version"] = match.group(1)
                        java_info["source"] = "gradle"
                        break
            except Exception:
                pass
        
        return java_info
    
    async def _detect_spring_boot(self, project_root: Path) -> Dict[str, Any]:
        """Detect Spring Boot framework and version."""
        spring_boot_info = {
            "detected": False,
            "version": "unknown",
            "starters": [],
            "actuator": False,
            "security": False
        }
        
        # Check dependencies for Spring Boot starters
        build_analysis = await self._analyze_build_system(project_root)
        
        for dep in build_analysis.get("dependencies", []):
            if isinstance(dep, dict):
                if "artifact_id" in dep:
                    artifact_id = dep["artifact_id"].lower()
                elif "identifier" in dep:
                    artifact_id = dep["identifier"].lower()
                else:
                    continue
            else:
                artifact_id = str(dep).lower()
            
            if "spring-boot" in artifact_id:
                spring_boot_info["detected"] = True
                
                if "spring-boot-starter-" in artifact_id:
                    starter_name = artifact_id.replace("spring-boot-starter-", "")
                    spring_boot_info["starters"].append(starter_name)
                
                if "starter-actuator" in artifact_id:
                    spring_boot_info["actuator"] = True
                
                if "starter-security" in artifact_id:
                    spring_boot_info["security"] = True
                
                # Try to extract version
                if "version" in dep and dep["version"]:
                    spring_boot_info["version"] = dep["version"]
        
        # Check for @SpringBootApplication annotation
        for java_file in project_root.rglob("*.java"):
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if '@SpringBootApplication' in content:
                    spring_boot_info["detected"] = True
                    break
            except Exception:
                continue
        
        return spring_boot_info
    
    async def _detect_database(self, project_root: Path) -> Dict[str, Any]:
        """Detect database technologies."""
        db_info = {
            "detected": False,
            "technologies": [],
            "jpa": False,
            "jdbc": False,
            "nosql": []
        }
        
        build_analysis = await self._analyze_build_system(project_root)
        
        for dep in build_analysis.get("dependencies", []):
            if isinstance(dep, dict):
                if "artifact_id" in dep:
                    artifact_id = dep["artifact_id"].lower()
                elif "identifier" in dep:
                    artifact_id = dep["identifier"].lower()
                else:
                    continue
            else:
                artifact_id = str(dep).lower()
            
            # Check for JPA/Hibernate
            if any(term in artifact_id for term in ["hibernate", "jpa", "javax.persistence"]):
                db_info["jpa"] = True
                db_info["detected"] = True
            
            # Check for JDBC drivers
            if any(term in artifact_id for term in ["jdbc", "mysql", "postgresql", "oracle", "sqlserver"]):
                db_info["jdbc"] = True
                db_info["detected"] = True
                
                if "mysql" in artifact_id:
                    db_info["technologies"].append("MySQL")
                elif "postgresql" in artifact_id:
                    db_info["technologies"].append("PostgreSQL")
                elif "oracle" in artifact_id:
                    db_info["technologies"].append("Oracle")
                elif "sqlserver" in artifact_id:
                    db_info["technologies"].append("SQL Server")
            
            # Check for NoSQL
            if any(term in artifact_id for term in ["mongodb", "redis", "cassandra", "neo4j"]):
                db_info["nosql"].append(artifact_id)
                db_info["detected"] = True
        
        return db_info
    
    async def _detect_testing_frameworks(self, project_root: Path) -> List[str]:
        """Detect testing frameworks."""
        frameworks = []
        
        build_analysis = await self._analyze_build_system(project_root)
        
        for dep in build_analysis.get("dependencies", []):
            if isinstance(dep, dict):
                if "artifact_id" in dep:
                    artifact_id = dep["artifact_id"].lower()
                elif "identifier" in dep:
                    artifact_id = dep["identifier"].lower()
                else:
                    continue
            else:
                artifact_id = str(dep).lower()
            
            if "junit" in artifact_id:
                frameworks.append("JUnit")
            elif "testng" in artifact_id:
                frameworks.append("TestNG")
            elif "mockito" in artifact_id:
                frameworks.append("Mockito")
            elif "spring-test" in artifact_id:
                frameworks.append("Spring Test")
            elif "testcontainers" in artifact_id:
                frameworks.append("TestContainers")
        
        # Remove duplicates
        return list(set(frameworks))
    
    async def _detect_other_frameworks(self, project_root: Path) -> List[str]:
        """Detect other frameworks and libraries."""
        frameworks = []
        
        build_analysis = await self._analyze_build_system(project_root)
        
        for dep in build_analysis.get("dependencies", []):
            if isinstance(dep, dict):
                if "artifact_id" in dep:
                    artifact_id = dep["artifact_id"].lower()
                elif "identifier" in dep:
                    artifact_id = dep["identifier"].lower()
                else:
                    continue
            else:
                artifact_id = str(dep).lower()
            
            if "spring" in artifact_id and "boot" not in artifact_id:
                frameworks.append("Spring Framework")
            elif "swagger" in artifact_id or "openapi" in artifact_id:
                frameworks.append("Swagger/OpenAPI")
            elif "lombok" in artifact_id:
                frameworks.append("Lombok")
            elif "mapstruct" in artifact_id:
                frameworks.append("MapStruct")
            elif "slf4j" in artifact_id or "logback" in artifact_id:
                frameworks.append("Logging (SLF4J/Logback)")
        
        # Remove duplicates
        return list(set(frameworks))
    
    async def _get_all_dependencies(self, project_root: Path) -> List[Dict[str, str]]:
        """Get all project dependencies."""
        build_analysis = await self._analyze_build_system(project_root)
        return build_analysis.get("dependencies", [])
    
    def _parse_properties(self, content: str) -> Dict[str, str]:
        """Parse Java properties file content."""
        properties = {}
        for line in content.split('\n'):
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
        return properties
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML content (simplified implementation)."""
        # This is a simplified YAML parser - in production, you'd use a proper YAML library
        yaml_dict = {}
        for line in content.split('\n'):
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                yaml_dict[key.strip()] = value.strip()
        return yaml_dict
