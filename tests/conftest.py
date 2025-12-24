"""Pytest configuration and fixtures for MCP Server tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_java_file(temp_dir):
    """Create a sample Java file for testing."""
    java_content = '''package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.demo.service.UserService;

/**
 * Main application class for the demo application.
 * This class serves as the entry point for the Spring Boot application.
 */
@SpringBootApplication
@RestController
public class DemoApplication {
    
    @Autowired
    private UserService userService;
    
    /**
     * Main method that starts the Spring Boot application.
     * @param args Command line arguments
     */
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
    
    /**
     * GET endpoint for greeting.
     * @return greeting message
     */
    @GetMapping("/hello")
    public String hello() {
        return "Hello, World!";
    }
    
    /**
     * GET endpoint for user count.
     * @return number of users
     */
    @GetMapping("/users/count")
    public int getUserCount() {
        return userService.getUserCount();
    }
}'''
    
    java_file = temp_dir / "DemoApplication.java"
    java_file.write_text(java_content)
    return java_file

@pytest.fixture
def sample_spring_project(temp_dir):
    """Create a sample Spring Boot project structure."""
    # Create directory structure
    src_dir = temp_dir / "src" / "main" / "java" / "com" / "example" / "demo"
    test_dir = temp_dir / "src" / "test" / "java" / "com" / "example" / "demo"
    resources_dir = temp_dir / "src" / "main" / "resources"
    
    src_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main application file
    main_app = src_dir / "DemoApplication.java"
    main_app.write_text('''package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}''')
    
    # Create controller directory first
    controller_dir = src_dir / "controller"
    controller_dir.mkdir(exist_ok=True)
    controller = controller_dir / "UserController.java"
    controller.write_text('''package com.example.demo.controller;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.demo.service.UserService;

@RestController
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping("/users")
    public String getUsers() {
        return userService.getAllUsers();
    }
}''')
    
    # Create service directory first
    service_dir = src_dir / "service"
    service_dir.mkdir(exist_ok=True)
    service = service_dir / "UserService.java"
    service.write_text('''package com.example.demo.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {
    
    public String getAllUsers() {
        return "[]";
    }
}''')
    
    # Create application.properties
    app_props = resources_dir / "application.properties"
    app_props.write_text('''server.port=8080
spring.application.name=demo-app
logging.level.com.example=DEBUG''')
    
    # Create pom.xml
    pom_xml = temp_dir / "pom.xml"
    pom_xml.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>demo</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    
    <properties>
        <java.version>11</java.version>
    </properties>
    
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
</project>''')
    
    return temp_dir

@pytest.fixture
def sample_config_files(temp_dir):
    """Create sample configuration files."""
    # application.properties
    props_file = temp_dir / "application.properties"
    props_file.write_text('''server.port=8080
spring.datasource.url=jdbc:mysql://localhost:3306/testdb
spring.datasource.username=root
spring.datasource.password=password
spring.jpa.hibernate.ddl-auto=update''')
    
    # application.yml
    yml_file = temp_dir / "application.yml"
    yml_file.write_text('''server:
  port: 8080
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/testdb
    username: root
    password: password
  jpa:
    hibernate:
      ddl-auto: update''')
    
    # build.gradle
    gradle_file = temp_dir / "build.gradle"
    gradle_file.write_text('''plugins {
    id 'org.springframework.boot' version '2.7.0'
    id 'io.spring.dependency-management' version '1.0.11.RELEASE'
    id 'java'
}

group = 'com.example'
version = '0.0.1-SNAPSHOT'
sourceCompatibility = '11'

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}''')
    
    return {
        'properties': props_file,
        'yml': yml_file,
        'gradle': gradle_file
    }

@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server instance for testing."""
    class MockMCPServer:
        def __init__(self):
            self.tools_called = []
            self.responses = {}
        
        def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            self.tools_called.append((name, arguments))
            return self.responses.get(name, {"mock": "response"})
        
        def set_response(self, tool_name: str, response: Dict[str, Any]):
            self.responses[tool_name] = response
    
    return MockMCPServer()
