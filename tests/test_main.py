"""Unit tests for MCP Server main module."""

import pytest
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.main import CLineMCPServer


class TestCLineMCPServer:
    """Test cases for CLineMCPServer class."""

    @pytest.fixture
    def mcp_server(self):
        """Create a CLineMCPServer instance for testing."""
        server = CLineMCPServer()
        return server

    @pytest.mark.asyncio
    async def test_server_initialization(self, mcp_server):
        """Test CLineMCPServer initialization."""
        assert mcp_server.server is not None
        assert hasattr(mcp_server, '_list_tools')
        assert hasattr(mcp_server, '_call_tool')

    @pytest.mark.asyncio
    async def test_tool_registration(self, mcp_server):
        """Test tool registration during server initialization."""
        # Check that tools are registered by calling list_tools
        tools = await mcp_server._list_tools()
        
        assert len(tools) > 0
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "analyze_code",
            "get_function_signatures",
            "list_files",
            "read_file",
            "generate_docs",
            "extract_comments",
            "get_project_structure",
            "detect_technologies"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_analyze_code_tool(self, mcp_server):
        """Test analyze_code tool functionality."""
        tools = await mcp_server._list_tools()
        
        analyze_tool = next(
            tool for tool in tools 
            if tool.name == "analyze_code"
        )
        
        assert analyze_tool.name == "analyze_code"
        assert analyze_tool.description is not None
        
        # Check input schema
        input_schema = analyze_tool.inputSchema
        assert "properties" in input_schema
        assert "path" in input_schema["properties"]
        assert "analysis_type" in input_schema["properties"]

    @pytest.mark.asyncio
    async def test_list_files_tool(self, mcp_server):
        """Test list_files tool functionality."""
        tools = await mcp_server._list_tools()
        
        list_files_tool = next(
            tool for tool in tools 
            if tool.name == "list_files"
        )
        
        assert list_files_tool.name == "list_files"
        assert list_files_tool.description is not None
        
        # Check input schema
        input_schema = list_files_tool.inputSchema
        assert input_schema.get("type") == "object"

    @pytest.mark.asyncio
    async def test_generate_docs_tool(self, mcp_server):
        """Test generate_docs tool functionality."""
        tools = await mcp_server._list_tools()
        
        docs_tool = next(
            tool for tool in tools 
            if tool.name == "generate_docs"
        )
        
        assert docs_tool.name == "generate_docs"
        assert docs_tool.description is not None

    @pytest.mark.asyncio
    async def test_get_project_structure_tool(self, mcp_server):
        """Test get_project_structure tool functionality."""
        tools = await mcp_server._list_tools()
        
        structure_tool = next(
            tool for tool in tools 
            if tool.name == "get_project_structure"
        )
        
        assert structure_tool.name == "get_project_structure"
        assert structure_tool.description is not None

    @pytest.mark.asyncio
    async def test_tool_call_analyze_code(self, mcp_server, sample_java_file):
        """Test calling analyze_code tool."""
        result = await mcp_server._call_tool(
            "analyze_code",
            {
                "path": str(sample_java_file),
                "analysis_type": "structure"
            }
        )
        
        assert len(result) > 0
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_list_files(self, mcp_server, temp_dir):
        """Test calling list_files tool."""
        # Create some test files
        (temp_dir / "test1.txt").write_text("test1")
        (temp_dir / "test2.txt").write_text("test2")
        
        result = await mcp_server._call_tool(
            "list_files",
            {
                "directory": str(temp_dir)
            }
        )
        
        assert len(result) > 0
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_generate_docs(self, mcp_server, sample_java_file):
        """Test calling generate_docs tool."""
        result = await mcp_server._call_tool(
            "generate_docs",
            {
                "target": str(sample_java_file),
                "format": "markdown"
            }
        )
        
        assert len(result) > 0
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_call_get_project_structure(self, mcp_server, sample_spring_project):
        """Test calling get_project_structure tool."""
        result = await mcp_server._call_tool(
            "get_project_structure",
            {
                "root_path": str(sample_spring_project)
            }
        )
        
        assert len(result) > 0
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_tool(self, mcp_server):
        """Test error handling for invalid tool calls."""
        result = await mcp_server._call_tool(
            "nonexistent_tool",
            {}
        )
        
        # Should handle error gracefully
        assert len(result) > 0
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_tool_descriptions_completeness(self, mcp_server):
        """Test that all tools have complete descriptions."""
        tools = await mcp_server._list_tools()
        
        for tool in tools:
            assert tool.name is not None, f"Tool {tool} missing name"
            assert tool.description is not None, f"Tool {tool} missing description"
            assert len(tool.description) > 0, f"Tool {tool} has empty description"

    @pytest.mark.asyncio
    async def test_tool_schema_validation(self, mcp_server):
        """Test tool input schemas are valid."""
        tools = await mcp_server._list_tools()
        
        for tool in tools:
            schema = tool.inputSchema
            assert schema.get("type") == "object", f"Tool {tool.name} schema not object type"

    def test_main_function_imports(self):
        """Test that main function can be imported and has expected attributes."""
        from mcp_server.main import main
        
        assert callable(main), "main should be a callable function"

    @pytest.mark.asyncio
    async def test_server_isolation(self, mcp_server):
        """Test that server instances are properly isolated."""
        server2 = CLineMCPServer()
        
        # Both should have the same tools
        tools1 = await mcp_server._list_tools()
        tools2 = await server2._list_tools()
        
        assert len(tools1) == len(tools2)
        
        tool_names1 = {tool.name for tool in tools1}
        tool_names2 = {tool.name for tool in tools2}
        assert tool_names1 == tool_names2

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_server, temp_dir):
        """Test that concurrent tool calls work properly."""
        import asyncio
        
        # Create test files
        files = []
        for i in range(3):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(str(file_path))
        
        # Make concurrent calls
        tasks = []
        for file_path in files:
            task = mcp_server._call_tool(
                "read_file",
                {
                    "file_path": file_path
                }
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All calls should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert len(result) > 0
            assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_tool_statelessness(self, mcp_server, sample_java_file):
        """Test that tool calls are stateless."""
        # First call
        result1 = await mcp_server._call_tool(
            "analyze_code",
            {
                "path": str(sample_java_file),
                "analysis_type": "structure"
            }
        )
        
        # Second call should give same result
        result2 = await mcp_server._call_tool(
            "analyze_code",
            {
                "path": str(sample_java_file),
                "analysis_type": "structure"
            }
        )
        
        # Results should be consistent
        assert result1[0].type == result2[0].type
        assert result1[0].type == "text"

    @pytest.mark.asyncio
    async def test_mixed_tool_operations(self, mcp_server, temp_dir):
        """Test mixing different tool operations."""
        # Create a Java file
        java_file = temp_dir / "Test.java"
        java_file.write_text('''
        @RestController
        public class TestController {
            @GetMapping("/test")
            public String test() { return "hello"; }
        }
        ''')
        
        # List files
        list_result = await mcp_server._call_tool(
            "list_files",
            {
                "directory": str(temp_dir)
            }
        )
        
        # Read file
        read_result = await mcp_server._call_tool(
            "read_file",
            {
                "file_path": str(java_file)
            }
        )
        
        # Analyze code
        code_result = await mcp_server._call_tool(
            "analyze_code",
            {
                "path": str(java_file),
                "analysis_type": "all"
            }
        )
        
        # Generate docs
        docs_result = await mcp_server._call_tool(
            "generate_docs",
            {
                "target": str(java_file),
                "format": "markdown"
            }
        )
        
        # All should succeed
        for result in [list_result, read_result, code_result, docs_result]:
            assert len(result) > 0
            assert result[0].type == "text"
