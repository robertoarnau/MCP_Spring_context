"""Service for high-level file management operations."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp_server.core.interfaces import FileSystemInterface
from mcp_server.services.java_service import JavaService

class FileService:
    """Business logic for file management."""
    
    def __init__(self, fs: FileSystemInterface, java_service: JavaService):
        self._fs = fs
        self._java_service = java_service

    async def list_files_with_metadata(self, directory: str, pattern: str = "*", recursive: bool = True) -> Dict[str, Any]:
        dir_path = Path(directory)
        if not await self._fs.exists(dir_path):
            return {"error": f"Directory does not exist: {directory}"}
            
        paths = await self._fs.list_dir(dir_path, pattern, recursive)
        files = []
        spring_boot_files = []
        config_files = []
        
        for p in paths:
            if await self._fs.is_file(p):
                info = self._fs.get_info(p)
                info["hash"] = await self._fs.calculate_hash(p)
                info["is_java_file"] = p.suffix == ".java"
                info["is_config_file"] = p.name in ['pom.xml', 'build.gradle', 'application.properties', 'application.yml']
                files.append(info)
                
                if info["is_java_file"]:
                    spring_boot_files.append(info)
                if info["is_config_file"]:
                    config_files.append(info)
                    
        return {
            "directory": directory,
            "total_files": len(files),
            "files": files,
            "spring_boot_files": spring_boot_files,
            "config_files": config_files,
            "spring_boot_structure": await self._java_service.analyze_spring_structure(dir_path)
        }

    async def read_file_with_analysis(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not await self._fs.exists(path):
            return {"error": f"File does not exist: {file_path}"}
            
        try:
            # First try reading a small chunk to check for binary
            binary_check = await self._fs.read_binary(path)
            if b'\x00' in binary_check[:1024]:
                content = f"<Binary file - {len(binary_check)} bytes>"
            else:
                content = await self._fs.read_file(path)
        except UnicodeDecodeError:
            binary = await self._fs.read_binary(path)
            content = f"<Binary file - {len(binary)} bytes>"
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}
            
        result = {
            "file_path": file_path,
            "content": content,
            "metadata": self._fs.get_info(path)
        }
        result["metadata"]["hash"] = await self._fs.calculate_hash(path)
        
        if path.suffix == ".java":
            result["java_analysis"] = await self._java_service.analyze_java_file(content)
        elif path.suffix in ['.xml', '.yml', '.yaml', '.properties']:
            result["config_analysis"] = await self._java_service.analyze_config_file(content, path.suffix)
            
        return result

    async def create_file(self, file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        path = Path(file_path)
        if await self._fs.exists(path) and not overwrite:
            return {"error": f"File already exists: {file_path}"}
            
        await self._fs.write_file(path, content)
        
        return {
            "success": True,
            "file_path": file_path,
            "message": f"File created successfully: {file_path}",
            "metadata": self._fs.get_info(path)
        }

    async def update_file(self, file_path: str, content: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not await self._fs.exists(path):
            return {"error": f"File does not exist: {file_path}"}
            
        backup_path = path.with_suffix(f"{path.suffix}.backup")
        await self._fs.copy_file(path, backup_path)
        await self._fs.write_file(path, content)
        
        return {
            "success": True,
            "file_path": file_path,
            "backup_path": str(backup_path),
            "message": f"File updated successfully: {file_path}",
            "metadata": self._fs.get_info(path)
        }

    async def delete_file(self, file_path: str, create_backup: bool = False) -> Dict[str, Any]:
        path = Path(file_path)
        if not await self._fs.exists(path):
            return {"error": f"File does not exist: {file_path}"}
            
        backup_path = None
        if create_backup:
            backup_dir = path.parent / ".backup"
            backup_path = backup_dir / path.name
            await self._fs.copy_file(path, backup_path)
            
        await self._fs.delete_file(path)
        
        return {
            "success": True,
            "file_path": file_path,
            "backup_path": str(backup_path) if backup_path else None,
            "message": f"File deleted successfully: {file_path}"
        }

    async def search_files(self, directory: str, search_term: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        dir_path = Path(directory)
        if not await self._fs.exists(dir_path):
            return {"error": f"Directory does not exist: {directory}"}
            
        results = []
        search_pattern = file_pattern if file_pattern else "*"
        
        for file_path in await self._fs.list_dir(dir_path, search_pattern, recursive=True):
            if await self._fs.is_file(file_path):
                try:
                    content = await self._fs.read_file(file_path)
                    if search_term.lower() in content.lower():
                        lines_with_matches = []
                        for i, line in enumerate(content.split('\n'), 1):
                            if search_term.lower() in line.lower():
                                lines_with_matches.append({
                                    "line_number": i,
                                    "content": line.strip()
                                })
                        results.append({
                            "file": str(file_path),
                            "matches": len(lines_with_matches),
                            "lines": lines_with_matches
                        })
                except (UnicodeDecodeError, Exception):
                    continue
                    
        return {
            "search_term": search_term,
            "directory": directory,
            "file_pattern": search_pattern,
            "total_matches": len(results),
            "files_with_matches": results
        }
