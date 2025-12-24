"""Unit tests for ProjectStructure class."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools.project_structure import ProjectStructure


class TestProjectStructure:
    """Test cases for ProjectStructure class."""

    @pytest.fixture
    def project_structure(self):
        """Create a ProjectStructure instance for testing."""
        return ProjectStructure()

    @pytest.mark.asyncio
    async def test_get_structure_basic(self, project_structure, sample_spring_project):
        """Test basic project structure analysis."""
        result = await project_structure.get_structure(str(sample_spring_project))
        
        assert result["project_name"] == sample_spring_project.name
        assert result["root_path"] == str(sample_spring_project)
        assert result["total_files"] > 0
        assert result["total_directories"] > 0
        assert "file_types" in result
        assert "directory_tree" in result
        assert "java_analysis" in result
        assert "spring_boot_analysis" in result
        assert "build_system_analysis" in result

    @pytest.mark.asyncio
    async def test_get_structure_with_file_sizes(self, project_structure, sample_spring_project):
        """Test project structure analysis with file sizes."""
        result = await project_structure.get_structure(str(sample_spring_project), include_file_sizes=True)
        
        assert result["total_size"] > 0
        for ext_type, info in result["file_types"].items():
            assert "total_size" in info
            assert info["total_size"] >= 0

    @pytest.mark.asyncio
    async def test_get_structure_with_depth_limit(self, project_structure, sample_spring_project):
        """Test project structure analysis with depth limit."""
        result = await project_structure.get_structure(str(sample_spring_project), depth=1)
        
        # Check that directory tree respects depth limit
        def check_depth(node, current_depth):
            if current_depth > 1:
                # Should not have children beyond depth 1
                assert len(node.get("children", [])) == 0
            else:
                for child in node.get("children", []):
                    check_depth(child, current_depth + 1)
        
        check_depth(result["directory_tree"], 0)

    @pytest.mark.asyncio
    async def test_get_structure_nonexistent_directory(self, project_structure):
        """Test structure analysis of non-existent directory."""
        result = await project_structure.get_structure("/nonexistent/directory")
        
        assert "error" in result
        assert "Project root does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_detect_technologies(self, project_structure, sample_spring_project):
        """Test technology detection."""
        result = await project_structure.detect_technologies(str(sample_spring_project))
        
        assert "java_version" in result
        assert "spring_boot" in result
        assert "build_system" in result
        assert "database" in result
        assert "testing_frameworks" in result
        assert "other_frameworks" in result
        assert "dependencies" in result

    @pytest.mark.asyncio
    async def test_detect_technologies_nonexistent(self, project_structure):
        """Test technology detection for non-existent project."""
        result = await project_structure.detect_technologies("/nonexistent/project")
        
        assert "error" in result
        assert "Project path does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_build_directory_tree(self, project_structure, temp_dir):
        """Test building directory tree."""
        # Create nested structure
        (temp_dir / "dir1").mkdir()
        (temp_dir / "dir1" / "subdir1").mkdir()
        (temp_dir / "dir2").mkdir()
        
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "dir1" / "file2.txt").write_text("content2")
        
        tree = await project_structure._build_directory_tree(temp_dir, 3, True)
        
        assert tree["name"] == temp_dir.name
        assert tree["type"] == "directory"
        assert len(tree["children"]) > 0
        
        # Find directories in children
        dirs = [child for child in tree["children"] if child["type"] == "directory"]
        files = [child for child in tree["children"] if child["type"] == "file"]
        
        assert len(dirs) >= 2  # dir1, dir2
        assert len(files) >= 1  # file1.txt

    @pytest.mark.asyncio
    async def test_analyze_java_structure(self, project_structure, sample_spring_project):
        """Test Java structure analysis."""
        java_analysis = await project_structure._analyze_java_structure(sample_spring_project)
        
        assert java_analysis["total_java_files"] > 0
        assert len(java_analysis["packages"]) > 0
        assert len(java_analysis["main_classes"]) > 0
        assert "spring_components" in java_analysis
        assert java_analysis["spring_components"]["controllers"][0] is not None

    @pytest.mark.asyncio
    async def test_analyze_spring_boot_structure(self, project_structure, sample_spring_project):
        """Test Spring Boot structure analysis."""
        spring_analysis = await project_structure._analyze_spring_boot_structure(sample_spring_project)
        
        assert spring_analysis["is_spring_boot_project"] is True
        assert spring_analysis["main_class"] is not None
        assert spring_analysis["application_config"] is not None
        assert len(spring_analysis["spring_annotations_found"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_build_system_maven(self, project_structure, sample_spring_project):
        """Test Maven build system analysis."""
        build_analysis = await project_structure._analyze_build_system(sample_spring_project)
        
        assert build_analysis["build_system"] == "maven"
        assert "pom.xml" in build_analysis["build_files"]
        assert len(build_analysis["dependencies"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_build_system_gradle(self, project_structure, sample_config_files):
        """Test Gradle build system analysis."""
        # Add some fake Java files to make it a project
        (sample_config_files["gradle"].parent / "src").mkdir()
        (sample_config_files["gradle"].parent / "src" / "Main.java").write_text("public class Main {}")
        
        build_analysis = await project_structure._analyze_build_system(sample_config_files["gradle"].parent)
        
        assert build_analysis["build_system"] == "gradle"
        assert "build.gradle" in build_analysis["build_files"]

    @pytest.mark.asyncio
    async def test_detect_java_version_maven(self, project_structure, sample_spring_project):
        """Test Java version detection from Maven."""
        java_info = await project_structure._detect_java_version(sample_spring_project)
        
        assert java_info["version"] == "11"  # From our sample pom.xml
        assert java_info["source"] == "maven"

    @pytest.mark.asyncio
    async def test_detect_java_version_gradle(self, project_structure, sample_config_files):
        """Test Java version detection from Gradle."""
        java_info = await project_structure._detect_java_version(sample_config_files["gradle"].parent)
        
        assert java_info["version"] == "11"  # From our sample build.gradle
        assert java_info["source"] == "gradle"

    @pytest.mark.asyncio
    async def test_detect_spring_boot(self, project_structure, sample_spring_project):
        """Test Spring Boot detection."""
        spring_boot_info = await project_structure._detect_spring_boot(sample_spring_project)
        
        assert spring_boot_info["detected"] is True
        assert len(spring_boot_info["starters"]) > 0
        assert "web" in spring_boot_info["starters"]  # From our pom.xml

    @pytest.mark.asyncio
    async def test_detect_database(self, project_structure, sample_spring_project):
        """Test database technology detection."""
        db_info = await project_structure._detect_database(sample_spring_project)
        
        assert db_info["jpa"] is True  # From spring-boot-starter-data-jpa
        assert len(db_info["technologies"]) > 0

    @pytest.mark.asyncio
    async def test_detect_testing_frameworks(self, project_structure, temp_dir):
        """Test testing framework detection."""
        # Create a Gradle file with test dependencies
        gradle_content = '''
        dependencies {
            testImplementation 'org.junit.jupiter:junit-jupiter'
            testImplementation 'org.mockito:mockito-core'
            testImplementation 'org.springframework.boot:spring-boot-starter-test'
        }
        '''
        gradle_file = temp_dir / "build.gradle"
        gradle_file.write_text(gradle_content)
        
        frameworks = await project_structure._detect_testing_frameworks(temp_dir)
        
        assert "JUnit" in frameworks
        assert "Mockito" in frameworks
        assert "Spring Test" in frameworks

    @pytest.mark.asyncio
    async def test_detect_other_frameworks(self, project_structure, temp_dir):
        """Test other framework detection."""
        # Create a Gradle file with various dependencies
        gradle_content = '''
        dependencies {
            implementation 'org.springframework:spring-core'
            implementation 'io.swagger:swagger-annotations'
            implementation 'org.projectlombok:lombok'
            implementation 'org.mapstruct:mapstruct'
            implementation 'org.slf4j:slf4j-api'
        }
        '''
        gradle_file = temp_dir / "build.gradle"
        gradle_file.write_text(gradle_content)
        
        frameworks = await project_structure._detect_other_frameworks(temp_dir)
        
        assert "Spring Framework" in frameworks
        assert "Swagger/OpenAPI" in frameworks
        assert "Lombok" in frameworks
        assert "MapStruct" in frameworks
        assert "Logging (SLF4J/Logback)" in frameworks

    def test_parse_properties(self, project_structure):
        """Test properties file parsing."""
        properties_content = '''
        server.port=8080
        spring.datasource.url=jdbc:mysql://localhost:3306/test
        # This is a comment
        logging.level.root=INFO
        '''
        
        properties = project_structure._parse_properties(properties_content)
        
        assert properties["server.port"] == "8080"
        assert properties["spring.datasource.url"] == "jdbc:mysql://localhost:3306/test"
        assert properties["logging.level.root"] == "INFO"
        assert "# This is a comment" not in properties

    def test_parse_yaml(self, project_structure):
        """Test YAML file parsing (simplified)."""
        yaml_content = '''
        server:
          port: 8080
        spring:
          datasource:
            url: jdbc:mysql://localhost:3306/test
        logging:
          level:
            root: INFO
        '''
        
        yaml = project_structure._parse_yaml(yaml_content)
        
        assert yaml["server"] == "8080"
        assert "spring" in yaml
        assert "logging" in yaml

    @pytest.mark.asyncio
    async def test_spring_indicators_detection(self, project_structure, temp_dir):
        """Test Spring Boot indicators detection."""
        # Create Spring Boot indicators
        (temp_dir / "src" / "main" / "java").mkdir(parents=True)
        (temp_dir / "src" / "main" / "resources").mkdir(parents=True)
        (temp_dir / "src" / "test" / "java").mkdir(parents=True)
        (temp_dir / "target").mkdir()
        
        java_file = temp_dir / "src" / "main" / "java" / "Application.java"
        java_file.write_text('''
        @SpringBootApplication
        public class Application {
            public static void main(String[] args) {
                SpringApplication.run(Application.class, args);
            }
        }
        ''')
        
        spring_analysis = await project_structure._analyze_spring_boot_structure(temp_dir)
        
        assert spring_analysis["is_spring_boot_project"] is True
        assert spring_analysis["has_main_sources"] is True
        assert spring_analysis["has_test_sources"] is True
        assert spring_analysis["has_resources"] is True

    @pytest.mark.asyncio
    async def test_file_types_analysis(self, project_structure, sample_spring_project):
        """Test file types analysis."""
        result = await project_structure.get_structure(str(sample_spring_project))
        
        file_types = result["file_types"]
        
        # Should have Java files
        assert ".java" in file_types
        assert file_types[".java"]["count"] > 0
        
        # Should have XML file (pom.xml)
        assert ".xml" in file_types
        assert file_types[".xml"]["count"] > 0

    @pytest.mark.asyncio
    async def test_java_package_extraction(self, project_structure, temp_dir):
        """Test Java package extraction."""
        # Create Java files with different packages
        com_dir = temp_dir / "com" / "example" / "app"
        org_dir = temp_dir / "org" / "test" / "lib"
        
        com_dir.mkdir(parents=True)
        org_dir.mkdir(parents=True)
        
        (com_dir / "Main.java").write_text("package com.example.app;\npublic class Main {}")
        (org_dir / "TestLib.java").write_text("package org.test.lib;\npublic class TestLib {}")
        
        java_analysis = await project_structure._analyze_java_structure(temp_dir)
        
        packages = java_analysis["packages"]
        assert "com.example.app" in packages
        assert "org.test.lib" in packages
        assert java_analysis["total_java_files"] == 2

    @pytest.mark.asyncio
    async def test_spring_components_classification(self, project_structure, temp_dir):
        """Test Spring components classification."""
        # Create different Spring components
        java_dir = temp_dir / "src" / "main" / "java" / "test"
        java_dir.mkdir(parents=True)
        
        # Controller
        controller_file = java_dir / "TestController.java"
        controller_file.write_text('''
        package test;
        @RestController
        public class TestController {
            @GetMapping("/test")
            public String test() { return ""; }
        }
        ''')
        
        # Service
        service_file = java_dir / "TestService.java"
        service_file.write_text('''
        package test;
        @Service
        public class TestService {
            public void doSomething() {}
        }
        ''')
        
        # Repository
        repository_file = java_dir / "TestRepository.java"
        repository_file.write_text('''
        package test;
        @Repository
        public class TestRepository {
            public void save() {}
        }
        ''')
        
        java_analysis = await project_structure._analyze_java_structure(temp_dir)
        
        components = java_analysis["spring_components"]
        assert len(components["controllers"]) == 1
        assert len(components["services"]) == 1
        assert len(components["repositories"]) == 1
        assert "TestController.java" in components["controllers"][0]

    @pytest.mark.asyncio
    async def test_dependency_extraction_maven(self, project_structure, temp_dir):
        """Test Maven dependency extraction."""
        pom_content = '''<?xml version="1.0"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0">
            <dependencies>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-web</artifactId>
                    <version>2.7.0</version>
                </dependency>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-data-jpa</artifactId>
                    <version>2.7.0</version>
                </dependency>
            </dependencies>
        </project>'''
        
        pom_file = temp_dir / "pom.xml"
        pom_file.write_text(pom_content)
        
        build_analysis = await project_structure._analyze_build_system(temp_dir)
        
        dependencies = build_analysis["dependencies"]
        assert len(dependencies) == 2
        
        web_dep = next(d for d in dependencies if d["artifact_id"] == "spring-boot-starter-web")
        assert web_dep["group_id"] == "org.springframework.boot"
        assert web_dep["version"] == "2.7.0"

    @pytest.mark.asyncio
    async def test_dependency_extraction_gradle(self, project_structure, temp_dir):
        """Test Gradle dependency extraction."""
        gradle_content = '''
        dependencies {
            implementation 'org.springframework.boot:spring-boot-starter-web:2.7.0'
            implementation 'org.springframework.boot:spring-boot-starter-data-jpa:2.7.0'
            testImplementation 'org.junit.jupiter:junit-jupiter:5.8.0'
        }
        '''
        
        gradle_file = temp_dir / "build.gradle"
        gradle_file.write_text(gradle_content)
        
        build_analysis = await project_structure._analyze_build_system(temp_dir)
        
        dependencies = build_analysis["dependencies"]
        assert len(dependencies) >= 3
        
        web_dep = next(d for d in dependencies if "spring-boot-starter-web" in d["identifier"])
        assert web_dep["identifier"] == "org.springframework.boot:spring-boot-starter-web:2.7.0"

    @pytest.mark.asyncio
    async def test_rest_endpoint_counting(self, project_structure, temp_dir):
        """Test REST endpoint counting."""
        java_dir = temp_dir / "src" / "main" / "java"
        java_dir.mkdir(parents=True)
        
        controller_file = java_dir / "TestController.java"
        controller_file.write_text('''
        @RestController
        public class TestController {
            @GetMapping("/test1")
            public String test1() { return ""; }
            
            @PostMapping("/test2")
            public String test2() { return ""; }
            
            @PutMapping("/test3")
            public String test3() { return ""; }
        }
        ''')
        
        spring_analysis = await project_structure._analyze_spring_boot_structure(temp_dir)
        
        assert spring_analysis["rest_endpoints"] == 3

    @pytest.mark.asyncio
    async def test_error_handling_malformed_xml(self, project_structure, temp_dir):
        """Test error handling for malformed XML."""
        malformed_pom = temp_dir / "pom.xml"
        malformed_pom.write_text("<?xml version='1.0'?><project><broken>")
        
        build_analysis = await project_structure._analyze_build_system(temp_dir)
        
        # Should handle the error gracefully
        assert build_analysis["build_system"] == "maven"  # Still detects Maven
        assert "dependencies" in build_analysis

    @pytest.mark.asyncio
    async def test_empty_project_analysis(self, project_structure, temp_dir):
        """Test analysis of empty project."""
        result = await project_structure.get_structure(str(temp_dir))
        
        assert result["total_files"] == 0
        assert result["total_directories"] == 0
        assert len(result["file_types"]) == 0
        assert result["directory_tree"]["children"] == []

    @pytest.mark.asyncio
    async def test_mixed_language_project(self, project_structure, temp_dir):
        """Test analysis of project with multiple file types."""
        # Create files with different extensions
        (temp_dir / "test.java").write_text("public class Test {}")
        (temp_dir / "test.py").write_text("def test(): pass")
        (temp_dir / "test.js").write_text("function test() {}")
        (temp_dir / "config.xml").write_text("<config></config>")
        (temp_dir / "config.yml").write_text("key: value")
        (temp_dir / "test.txt").write_text("plain text")
        
        result = await project_structure.get_structure(str(temp_dir))
        
        file_types = result["file_types"]
        expected_extensions = {".java", ".py", ".js", ".xml", ".yml", ".txt"}
        
        for ext in expected_extensions:
            assert ext in file_types
            assert file_types[ext]["count"] == 1
