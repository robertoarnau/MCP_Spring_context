---
trigger: always_on
---

# Reglas de Programación: Stack Python OOP & MCP

## 1. Estilo de Código y POO
- **Paradigma:** Estrictamente Orientado a Objetos (OOP). Evita scripts sueltos o funciones globales fuera de clases (excepto decoradores de herramientas MCP).
- **Principios SOLID:** Aplica rigurosamente, especialmente el Principio de Inversión de Dependencias (DIP).
- **Type Hinting:** Obligatorio en todos los métodos y atributos (`def method(self, arg: str) -> int:`).
- **Docstrings:** Estilo Google o NumPy para todas las clases y métodos públicos.

## 2. Inyección de Dependencias (DI)
- **Regla de Oro:** NUNCA instancies dependencias (servicios, clientes API, repositorios) dentro de una clase. Inyéctalas siempre a través del `__init__`.
- **Protocolos:** Usa `typing.Protocol` o Clases Abstractas (`abc.ABC`) para definir interfaces de dependencias. Las clases concretas no deben depender de otras clases concretas.
- **Contenedores:** Si la complejidad crece, centraliza la construcción de objetos en un "Container" o "Factory" en el `main` o punto de entrada, manteniendo el resto del código agnóstico.

## 3. Reglas Específicas por Librería

### MCP (Model Context Protocol) >= 1.0.0
- **Herramientas (Tools):** Define la lógica de negocio en Servicios (Clases). Usa las funciones decoradas con `@mcp.tool` solo como "Controladores" o "Entry Points" que llaman a estos servicios.
- **FastMCP DI:** Si usas `FastMCP`, aprovecha su sistema de inyección inspirado en FastAPI (si está disponible en tu versión) o usa closures/partials para inyectar el servicio en la tool.
- **Contexto:** Gestiona el ciclo de vida del servidor MCP (`mcp.server`) separado de la lógica de negocio.

### Asincronía (aiofiles, asyncio)
- **Async/Await:** Usa `async def` para todas las operaciones I/O (lectura de archivos, git, red).
- **Aiofiles:** Inyecta gestores de archivos o crea un `FileService` abstracto. No uses `open()` nativo directamente en la lógica de negocio; usa `aiofiles` dentro de un adaptador inyectado.

### GitPython
- **Wrapper:** Envuelve `git.Repo` y operaciones de GitPython en una clase propia (ej. `GitRepositoryService`). Esto facilita el mocking en tests y evita acoplar tu lógica a la API de GitPython.

## 4. Testing (pytest, pytest-asyncio, pytest-mock)
- **Fixtures:** Usa fixtures de `pytest` como tu mecanismo de Inyección de Dependencias para tests.
- **Mocking:** Usa `pytest-mock` (`mocker`) para simular las interfaces (Protocolos) definidas, nunca mockees la implementación concreta si puedes evitarlo.
- **Async Tests:** Decora los tests asíncronos con `@pytest.mark.asyncio`.
- **Coverage:** Asegura que `pytest-cov` cubra las ramas lógicas de tus servicios, no solo las definiciones de tools.