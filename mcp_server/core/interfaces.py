"""Core interfaces for the MCP server using Protocols."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pathlib import Path

@runtime_checkable
class FileSystemInterface(Protocol):
    """Interface for file system operations."""
    
    async def read_file(self, path: Path) -> str:
        """Read file content as string."""
        ...
        
    async def read_binary(self, path: Path) -> bytes:
        """Read file content as bytes."""
        ...
        
    async def write_file(self, path: Path, content: str) -> None:
        """Write string content to file."""
        ...
        
    async def copy_file(self, src: Path, dst: Path) -> None:
        """Copy a file."""
        ...
        
    async def delete_file(self, path: Path) -> None:
        """Delete a file."""
        ...
        
    async def exists(self, path: Path) -> bool:
        """Check if path exists."""
        ...
        
    async def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        ...
        
    async def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        ...
        
    async def list_dir(self, path: Path, pattern: str = "*", recursive: bool = False) -> List[Path]:
        """List files and directories."""
        ...

    def get_info(self, path: Path) -> Dict[str, Any]:
        """Get file/directory info (sync)."""
        ...

    async def calculate_hash(self, path: Path) -> str:
        """Calculate file hash."""
        ...
