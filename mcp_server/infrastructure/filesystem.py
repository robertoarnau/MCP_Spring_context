"""Concrete implementation of FileSystemInterface using aiofiles."""

import aiofiles
import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp_server.core.interfaces import FileSystemInterface

class AIOFileSystem(FileSystemInterface):
    """File system implementation using aiofiles for async I/O."""
    
    async def read_file(self, path: Path) -> str:
        async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
            return await f.read()
            
    async def read_binary(self, path: Path) -> bytes:
        async with aiofiles.open(path, mode='rb') as f:
            return await f.read()
            
    async def write_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
            await f.write(content)

    async def copy_file(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
            
    async def delete_file(self, path: Path) -> None:
        if await self.is_file(path):
            os.unlink(path)
        elif await self.is_dir(path):
            shutil.rmtree(path)
            
    async def exists(self, path: Path) -> bool:
        return path.exists()
        
    async def is_dir(self, path: Path) -> bool:
        return path.is_dir()
        
    async def is_file(self, path: Path) -> bool:
        return path.is_file()
        
    async def list_dir(self, path: Path, pattern: str = "*", recursive: bool = False) -> List[Path]:
        if recursive:
            return list(path.rglob(pattern))
        return list(path.glob(pattern))

    def get_info(self, path: Path) -> Dict[str, Any]:
        """Get comprehensive file information."""
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "size": stat.st_size,
            "size_human": self._format_size(stat.st_size),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": path.suffix,
            "mime_type": mimetypes.guess_type(str(path))[0],
            "is_java_file": path.suffix == '.java',
            "is_config_file": path.name in ['pom.xml', 'build.gradle', 'application.properties', 'application.yml', 'application.yaml', 'settings.gradle'],
            "hash": self._calculate_hash_sync(path)
        }

    def _calculate_hash_sync(self, path: Path) -> str:
        """Synchronous hash calculation for metadata."""
        try:
            hash_md5 = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    async def calculate_hash(self, path: Path) -> str:
        """Calculate MD5 hash of file."""
        try:
            hash_md5 = hashlib.md5()
            async with aiofiles.open(path, "rb") as f:
                while chunk := await f.read(4096):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format using base 1000 for compatibility with existing tests."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1000.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1000.0
        return f"{size_bytes:.1f} TB"
