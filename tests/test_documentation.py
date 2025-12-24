"""Unit tests for Documentation class."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools.documentation import Documentation


class TestDocumentation:
    """Test cases for Documentation class."""

    @pytest.fixture
    def documentation(self):
        """Create a Documentation instance for testing."""
        return Documentation()

    @pytest.mark.asyncio
    async def test_generate_docs_file(self, documentation, sample_java_file):
        """Test generating documentation for a single file."""
        result = await documentation.generate_docs(str(sample_java_file), "markdown")
        
        assert result["file"] == str(sample_java_file)
        assert result["package"] == "com.example.demo"
        assert len(result["imports"]) > 0
        assert result["class_info"]["name"] == "DemoApplication"
        assert len(result["methods"]) > 0
        assert result["spring_info"]["is_spring_component"] is True
        assert "formatted" in result

    @pytest.mark.asyncio
    async def test_generate_docs_project(self, documentation, sample_spring_project):
        """Test generating documentation for a project."""
        result = await documentation.generate_docs(str(sample_spring_project), "markdown")
        
        assert result["project_name"] == sample_spring_project.name
        assert result["project_path"] == str(sample_spring_project)
        assert "structure" in result
        assert "api_documentation" in result
        assert "generated_at" in result
        assert "formatted" in result

    @pytest.mark.asyncio
    async def test_generate_docs_html_format(self, documentation, sample_java_file):
        """Test generating documentation in HTML format."""
        result = await documentation.generate_docs(str(sample_java_file), "html")
        
        assert "formatted" in result
        assert "<!DOCTYPE html>" in result["formatted"]
        assert "<html>" in result["formatted"]

    @pytest.mark.asyncio
    async def test_generate_docs_json_format(self, documentation, sample_java_file):
        """Test generating documentation in JSON format."""
        result = await documentation.generate_docs(str(sample_java_file), "json")
        
        assert "formatted" not in result  # JSON returns raw data
        assert result["class_info"]["name"] == "DemoApplication"

    @pytest.mark.asyncio
    async def test_generate_docs_nonexistent_target(self, documentation):
        """Test generating documentation for non-existent target."""
        result = await documentation.generate_docs("/nonexistent/file.java")
        
        assert "error" in result
        assert "Target does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_comments(self, documentation, sample_java_file):
        """Test extracting comments from Java file."""
        result = await documentation.extract_comments(str(sample_java_file))
        
        assert result["file"] == str(sample_java_file)
        assert result["total_lines"] > 0
        assert len(result["comments"]) > 0
        assert "javadoc" in result
        assert "spring_endpoints" in result

    @pytest.mark.asyncio
    async def test_extract_comments_without_docstrings(self, documentation, sample_java_file):
        """Test extracting comments without docstrings."""
        result = await documentation.extract_comments(str(sample_java_file), include_docstrings=False)
        
        assert "javadoc" not in result
        assert len(result["comments"]) > 0

    @pytest.mark.asyncio
    async def test_extract_comments_nonexistent_file(self, documentation):
        """Test extracting comments from non-existent file."""
        result = await documentation.extract_comments("/nonexistent/file.java")
        
        assert "error" in result
        assert "File does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_comments_non_java_file(self, documentation, temp_dir):
        """Test extracting comments from non-Java file."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("// This is a comment\nSome text")
        
        result = await documentation.extract_comments(str(txt_file))
        
        assert "error" in result
        assert "not a Java file" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_javadoc(self, documentation):
        """Test Javadoc extraction from Java content."""
        java_content = '''
        /**
         * This is a class documentation.
         * @param name the name parameter
         * @return string result
         * @throws Exception if something goes wrong
         */
        public class TestClass {
            /**
             * Method documentation.
             * @param input input parameter
             * @return processed result
             */
            public String process(String input) {
                return input;
            }
        }
        '''
        
        result = documentation._extract_javadoc(java_content)
        
        assert len(result["class_documentation"]) > 0
        assert len(result["method_documentation"]) > 0
        
        class_doc = result["class_documentation"][0]
        assert class_doc["class"] == "TestClass"
        assert len(class_doc["parameters"]) > 0
        assert class_doc["returns"] is not None
        assert len(class_doc["throws"]) > 0

    def test_clean_javadoc(self, documentation):
        """Test Javadoc content cleaning."""
        javadoc_content = '''
        * This is a Javadoc comment.
        * It spans multiple lines.
        * With asterisks at the beginning.
        '''
        
        cleaned = documentation._clean_javadoc(javadoc_content)
        
        assert "*" not in cleaned
        assert "Javadoc comment" in cleaned
        assert "multiple lines" in cleaned

    def test_extract_javadoc_params(self, documentation):
        """Test extracting @param tags from Javadoc."""
        doc_content = '''
        * @param name the name parameter
        * @param age the age parameter
        * @param address the address parameter
        '''
        
        params = documentation._extract_javadoc_params(doc_content)
        
        assert len(params) == 3
        assert params[0]["name"] == "name"
        assert params[0]["description"] == "the name parameter"
        assert params[1]["name"] == "age"
        assert params[2]["name"] == "address"

    def test_extract_javadoc_return(self, documentation):
        """Test extracting @return tag from Javadoc."""
        doc_content_with_return = '''
        * @return processed string result
        '''
        
        doc_content_no_return = '''
        * @param input input parameter
        '''
        
        result_with_return = documentation._extract_javadoc_return(doc_content_with_return)
        result_no_return = documentation._extract_javadoc_return(doc_content_no_return)
        
        assert result_with_return == "processed string result"
        assert result_no_return is None

    def test_extract_javadoc_throws(self, documentation):
        """Test extracting @throws tags from Javadoc."""
        doc_content = '''
        * @throws IOException if file cannot be read
        * @throws IllegalArgumentException if parameter is null
        '''
        
        throws = documentation._extract_javadoc_throws(doc_content)
        
        assert len(throws) == 2
        assert throws[0]["exception"] == "IOException"
        assert throws[0]["description"] == "if file cannot be read"
        assert throws[1]["exception"] == "IllegalArgumentException"

    @pytest.mark.asyncio
    async def test_extract_spring_endpoints(self, documentation):
        """Test extracting Spring REST endpoints."""
        java_content = '''
        @RestController
        public class UserController {
            @GetMapping("/users")
            public List<User> getUsers() { return null; }
            
            @PostMapping("/users")
            public User createUser(@RequestBody User user) { return user; }
            
            @PutMapping("/users/{id}")
            public User updateUser(@PathVariable Long id, @RequestBody User user) { return user; }
            
            @DeleteMapping("/users/{id}")
            public void deleteUser(@PathVariable Long id) {}
            
            @RequestMapping(value = "/admin", method = RequestMethod.GET)
            public String admin() { return "admin"; }
        }
        '''
        
        endpoints = await documentation._extract_spring_endpoints(java_content)
        
        assert len(endpoints) == 5
        
        get_endpoint = next(e for e in endpoints if e["method_name"] == "getUsers")
        assert get_endpoint["http_method"] == "GET"
        assert get_endpoint["path"] == "/users"
        assert get_endpoint["return_type"] == "List<User>"
        
        post_endpoint = next(e for e in endpoints if e["method_name"] == "createUser")
        assert post_endpoint["http_method"] == "POST"
        assert post_endpoint["path"] == "/users"
        
        delete_endpoint = next(e for e in endpoints if e["method_name"] == "deleteUser")
        assert delete_endpoint["http_method"] == "DELETE"

    def test_find_line_number(self, documentation):
        """Test finding line number of text in content."""
        content = '''line 1
        line 2 with search text
        line 3
        line 4 with search text again'''
        
        line_num = documentation._find_line_number(content, "search text")
        assert line_num == 2
        
        not_found = documentation._find_line_number(content, "not found")
        assert not_found == 0

    @pytest.mark.asyncio
    async def test_extract_class_info(self, documentation):
        """Test extracting class information."""
        java_content = '''
        @RestController
        @RequestMapping("/api")
        public class UserController extends BaseController implements UserInterface {
            @Autowired
            private UserService userService;
            
            private String className;
        }
        '''
        
        class_info = await documentation._extract_class_info(java_content)
        
        assert class_info["name"] == "UserController"
        assert class_info["type"] == "class"
        assert "@RestController" in class_info["annotations"]
        assert "@RequestMapping" in class_info["annotations"]
        assert class_info["extends"] == ["BaseController"]
        assert "UserInterface" in class_info["implements"]
        assert len(class_info["fields"]) >= 2

    @pytest.mark.asyncio
    async def test_extract_methods_info(self, documentation):
        """Test extracting method information."""
        java_content = '''
        public class TestClass {
            @GetMapping("/test")
            public String testMethod(@RequestParam String param) { return ""; }
            
            @PostMapping("/create")
            @Transactional
            public User createUser(@RequestBody User user, @RequestParam String action) throws IOException {
                return user;
            }
            
            private void privateMethod() {}
        }
        '''
        
        methods = await documentation._extract_methods_info(java_content)
        
        assert len(methods) >= 3
        
        public_method = next(m for m in methods if m["name"] == "testMethod")
        assert public_method["return_type"] == "String"
        assert "@GetMapping" in public_method["annotations"]
        assert len(public_method["parameters"]) == 1
        assert public_method["parameters"][0]["name"] == "param"
        
        create_method = next(m for m in methods if m["name"] == "createUser")
        assert create_method["return_type"] == "User"
        assert "@PostMapping" in create_method["annotations"]
        assert "@Transactional" in create_method["annotations"]
        assert len(create_method["parameters"]) == 2
        assert len(create_method["throws"]) > 0

    @pytest.mark.asyncio
    async def test_extract_spring_info(self, documentation):
        """Test extracting Spring-specific information."""
        java_content = '''
        @RestController
        @RequestMapping("/api")
        public class TestController {
            @GetMapping("/test")
            public String test() { return ""; }
        }
        '''
        
        spring_info = await documentation._extract_spring_info(java_content)
        
        assert spring_info["is_spring_component"] is True
        assert spring_info["component_type"] == "Controller"
        assert "@RestController" in spring_info["annotations"]
        assert "@RequestMapping" in spring_info["annotations"]

    @pytest.mark.asyncio
    async def test_analyze_project_structure(self, documentation, sample_spring_project):
        """Test project structure analysis."""
        structure = await documentation._analyze_project_structure(sample_spring_project)
        
        assert structure["is_maven"] is True
        assert structure["total_java_files"] > 0
        assert structure["has_main_class"] is True

    @pytest.mark.asyncio
    async def test_analyze_configuration(self, documentation, sample_spring_project):
        """Test configuration analysis."""
        config = await documentation._analyze_configuration(sample_spring_project)
        
        assert "application_properties" in config
        assert len(config["application_properties"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_controllers(self, documentation, sample_spring_project):
        """Test controller analysis."""
        controllers = await documentation._analyze_controllers(sample_spring_project)
        
        assert len(controllers) > 0
        controller = controllers[0]
        assert "file" in controller
        assert "endpoints" in controller

    @pytest.mark.asyncio
    async def test_analyze_services(self, documentation, sample_spring_project):
        """Test service analysis."""
        services = await documentation._analyze_services(sample_spring_project)
        
        assert len(services) > 0
        service = services[0]
        assert service["name"] == "UserService"

    @pytest.mark.asyncio
    async def test_analyze_repositories(self, documentation, temp_dir):
        """Test repository analysis."""
        # Create a repository file
        repo_content = '''
        package com.example.demo.repository;
        
        import org.springframework.data.jpa.repository.JpaRepository;
        import org.springframework.stereotype.Repository;
        
        @Repository
        public interface UserRepository extends JpaRepository<User, Long> {
        }
        '''
        
        repo_file = temp_dir / "UserRepository.java"
        repo_file.write_text(repo_content)
        
        repositories = await documentation._analyze_repositories(temp_dir)
        
        assert len(repositories) > 0
        repository = repositories[0]
        assert repository["name"] == "UserRepository"

    @pytest.mark.asyncio
    async def test_analyze_entities(self, documentation, temp_dir):
        """Test entity analysis."""
        # Create an entity file
        entity_content = '''
        package com.example.demo.entity;
        
        import javax.persistence.Entity;
        import javax.persistence.Table;
        import javax.persistence.Id;
        
        @Entity
        @Table(name = "users")
        public class User {
            @Id
            private Long id;
        }
        '''
        
        entity_file = temp_dir / "User.java"
        entity_file.write_text(entity_content)
        
        entities = await documentation._analyze_entities(temp_dir)
        
        assert len(entities) > 0
        entity = entities[0]
        assert entity["name"] == "User"

    @pytest.mark.asyncio
    async def test_generate_api_docs(self, documentation, temp_dir):
        """Test API documentation generation."""
        # Create controller with endpoints
        controller_content = '''
        @RestController
        public class TestController {
            @GetMapping("/users")
            public String getUsers() { return ""; }
            
            @PostMapping("/users")
            public User createUser() { return null; }
        }
        '''
        
        controller_file = temp_dir / "TestController.java"
        controller_file.write_text(controller_content)
        
        api_docs = await documentation._generate_api_docs(temp_dir)
        
        assert len(api_docs) > 0
        assert api_docs[0]["controller"] == "TestController"
        assert len(api_docs) == 2  # Two endpoints

    @pytest.mark.asyncio
    async def test_format_as_markdown(self, documentation):
        """Test markdown formatting."""
        doc = {
            "class_info": {
                "name": "TestClass",
                "annotations": ["@RestController"],
                "methods": [
                    {
                        "name": "testMethod",
                        "return_type": "String",
                        "parameters": [{"type": "String", "name": "param"}],
                        "annotations": ["@GetMapping"],
                        "throws": []
                    }
                ]
            },
            "package": "com.example.test",
            "spring_info": {
                "is_spring_component": True,
                "component_type": "Controller"
            }
        }
        
        markdown = await documentation._format_as_markdown(doc)
        
        assert "# TestClass" in markdown
        assert "`@RestController`" in markdown
        assert "## Methods" in markdown
        assert "String testMethod(String param)" in markdown

    @pytest.mark.asyncio
    async def test_format_project_as_markdown(self, documentation):
        """Test project markdown formatting."""
        doc = {
            "project_name": "Demo Project",
            "generated_at": "2023-01-01T00:00:00",
            "structure": {
                "is_maven": True,
                "total_java_files": 5,
                "total_test_files": 2
            },
            "api_documentation": [
                {
                    "http_method": "GET",
                    "path": "/users",
                    "controller": "UserController",
                    "method_name": "getUsers",
                    "return_type": "User[]"
                }
            ]
        }
        
        markdown = await documentation._format_project_as_markdown(doc)
        
        assert "# Demo Project API Documentation" in markdown
        assert "## Project Overview" in markdown
        assert "## API Endpoints" in markdown
        assert "GET /users" in markdown

    @pytest.mark.asyncio
    async def test_format_as_html(self, documentation):
        """Test HTML formatting."""
        doc = {
            "class_info": {"name": "TestClass"},
            "project_name": "Test Project",
            "generated_at": "2023-01-01T00:00:00"
        }
        
        html = await documentation._format_as_html(doc)
        
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<title>" in html
        assert "</body>" in html
        assert "</html>" in html

    @pytest.mark.asyncio
    async def test_class_info_annotations_extraction(self, documentation):
        """Test extracting class annotations properly."""
        java_content = '''
        @RestController
        @RequestMapping("/api")
        @CrossOrigin
        public class TestController {
            // methods
        }
        '''
        
        class_info = await documentation._extract_class_info(java_content)
        
        assert len(class_info["annotations"]) >= 3
        assert "@RestController" in class_info["annotations"]
        assert "@RequestMapping" in class_info["annotations"]
        assert "@CrossOrigin" in class_info["annotations"]

    @pytest.mark.asyncio
    async def test_field_extraction(self, documentation):
        """Test extracting class fields."""
        java_content = '''
        public class TestClass {
            @Autowired
            private Service service;
            
            @Value("${test.value}")
            private String testValue;
            
            public static final String CONSTANT = "value";
            
            private int count;
        }
        '''
        
        class_info = await documentation._extract_class_info(java_content)
        
        fields = class_info["fields"]
        assert len(fields) >= 4
        
        # Check field properties
        service_field = next(f for f in fields if f["name"] == "service")
        assert service_field["type"] == "Service"
        assert "@Autowired" in service_field["annotations"]
        
        test_value_field = next(f for f in fields if f["name"] == "testValue")
        assert test_value_field["type"] == "String"
        assert "@Value" in test_value_field["annotations"]
