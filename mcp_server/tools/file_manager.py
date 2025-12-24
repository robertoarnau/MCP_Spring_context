"""File management tools for CLine MCP Server - Java/Spring Boot focused."""

import logging
from typing import Any, Dict, Optional
from mcp_server.services.file_service import FileService
from mcp_server.services.java_service import JavaService

logger = logging.getLogger(__name__)

class FileManager:
    """Provides file management capabilities by delegating to specialized services."""
    
    def __init__(self, file_service: FileService, java_service: JavaService):
        """Initialize the FileManager with injected services."""
        self._file_service = file_service
        self._java_service = java_service
    
    async def list_files(self, directory: str, pattern: Optional[str] = None, recursive: bool = True) -> Dict[str, Any]:
        """List files in directory with filtering options."""
        return await self._file_service.list_files_with_metadata(
            directory, 
            pattern or "*", 
            recursive
        )
    
    async def read_file(self, file_path: str, include_metadata: bool = True) -> Dict[str, Any]:
        """Read file content with optional metadata and analysis."""
        result = await self._file_service.read_file_with_analysis(file_path)
        if "metadata" in result and "error" not in result:
            # Flatten some metadata for backward compatibility if needed
            result["metadata"]["is_java_file"] = result["metadata"].get("is_java_file", False)
        return result

    async def create_file(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """Create a new file."""
        return await self._file_service.create_file(file_path, content, overwrite)

    async def update_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Update an existing file."""
        return await self._file_service.update_file(file_path, content)

    async def delete_file(self, file_path: str, create_backup: bool = False) -> Dict[str, Any]:
        """Delete a file."""
        return await self._file_service.delete_file(file_path, create_backup)

    async def search_files(self, directory: str, search_term: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Search for files containing specific text."""
        return await self._file_service.search_files(directory, search_term, file_pattern)

    # Private methods for test backward compatibility
    def _format_size(self, size_bytes: int) -> str:
        return self._file_service._fs._format_size(size_bytes)

    def _get_file_info(self, path) -> Dict[str, Any]:
        from pathlib import Path
        return self._file_service._fs.get_info(Path(path))

    async def _analyze_spring_structure(self, path) -> Dict[str, Any]:
        from pathlib import Path
        return await self._java_service.analyze_spring_structure(Path(path))

    async def _analyze_java_file_structure(self, content: str) -> Dict[str, Any]:
        return await self._java_service.analyze_java_file(content)

    async def _analyze_config_file(self, content: str, file_type: str) -> Dict[str, Any]:
        return await self._java_service.analyze_config_file(content, file_type)

    async def _validate_java_syntax(self, content: str) -> Dict[str, Any]:
        return self._java_service.validate_java_syntax(content)
