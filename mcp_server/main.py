"""Main MCP Server for CLine Development Context Provider."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.code_analyzer import CodeAnalyzer
from .tools.file_manager import FileManager
from .tools.documentation import Documentation
from .tools.project_structure import ProjectStructure

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

class CLineMCPServer:
    """MCP Server for providing development context to CLine."""
    
    def __init__(self):
        """Initialize the MCP server with all tools."""
        self.server = Server("cline-context-provider")
        self.code_analyzer = CodeAnalyzer()
        self.file_manager = FileManager()
        self.documentation = Documentation()
        self.project_structure = ProjectStructure()
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools with the MCP server."""
        
        # Code Analysis Tools
        self.server.list_tools = self._list_tools
        self.server.call_tool = self._call_tool
    
    async def _list_tools(self) -> List[Tool]:
        """Return list of available tools."""
        return [
            # Code Analysis Tools
            Tool(
                name="analyze_code",
                description="Analyze code structure, dependencies, and quality",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to file or directory to analyze"},
                        "analysis_type": {"type": "string", "enum": ["structure", "dependencies", "quality", "all"], "default": "all"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="get_function_signatures",
                description="Extract function signatures from a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "language": {"type": "string", "description": "Programming language"}
                    },
                    "required": ["file_path"]
                }
            ),
            
            # File Management Tools
            Tool(
                name="list_files",
                description="List files in directory with filtering options",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Directory path"},
                        "pattern": {"type": "string", "description": "File pattern (e.g., *.py)"},
                        "recursive": {"type": "boolean", "default": True}
                    },
                    "required": ["directory"]
                }
            ),
            Tool(
                name="read_file",
                description="Read file content with metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "include_metadata": {"type": "boolean", "default": True}
                    },
                    "required": ["file_path"]
                }
            ),
            
            # Documentation Tools
            Tool(
                name="generate_docs",
                description="Generate documentation for code or project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "File or directory to document"},
                        "format": {"type": "string", "enum": ["markdown", "html", "json"], "default": "markdown"}
                    },
                    "required": ["target"]
                }
            ),
            Tool(
                name="extract_comments",
                description="Extract comments and docstrings from code",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "include_docstrings": {"type": "boolean", "default": True}
                    },
                    "required": ["file_path"]
                }
            ),
            
            # Project Structure Tools
            Tool(
                name="get_project_structure",
                description="Get detailed project structure and overview",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "root_path": {"type": "string", "description": "Root directory path"},
                        "depth": {"type": "integer", "default": 3},
                        "include_file_sizes": {"type": "boolean", "default": False}
                    },
                    "required": ["root_path"]
                }
            ),
            Tool(
                name="detect_technologies",
                description="Detect technologies and frameworks used in project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string", "description": "Path to project directory"}
                    },
                    "required": ["project_path"]
                }
            )
        ]
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute a tool call."""
        try:
            if name == "analyze_code":
                result = await self.code_analyzer.analyze(
                    arguments.get("path"),
                    arguments.get("analysis_type", "all")
                )
            elif name == "get_function_signatures":
                result = await self.code_analyzer.get_function_signatures(
                    arguments.get("file_path"),
                    arguments.get("language")
                )
            elif name == "list_files":
                result = await self.file_manager.list_files(
                    arguments.get("directory"),
                    arguments.get("pattern"),
                    arguments.get("recursive", True)
                )
            elif name == "read_file":
                result = await self.file_manager.read_file(
                    arguments.get("file_path"),
                    arguments.get("include_metadata", True)
                )
            elif name == "generate_docs":
                result = await self.documentation.generate_docs(
                    arguments.get("target"),
                    arguments.get("format", "markdown")
                )
            elif name == "extract_comments":
                result = await self.documentation.extract_comments(
                    arguments.get("file_path"),
                    arguments.get("include_docstrings", True)
                )
            elif name == "get_project_structure":
                result = await self.project_structure.get_structure(
                    arguments.get("root_path"),
                    arguments.get("depth", 3),
                    arguments.get("include_file_sizes", False)
                )
            elif name == "detect_technologies":
                result = await self.project_structure.detect_technologies(
                    arguments.get("project_path")
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(type="text", text=str(result))]
            
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Main entry point for the MCP server."""
    server_instance = CLineMCPServer()
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
