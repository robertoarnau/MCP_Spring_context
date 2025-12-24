# ☕ CLine MCP Server: Tu Copiloto para Java & Spring Boot

¡Bienvenido! Este servidor implementa el **Model Context Protocol (MCP)** diseñado específicamente para potenciar el desarrollo en ecosistemas **Java** y **Spring Boot**.

Piensa en esta herramienta como un puente inteligente entre tu LLM (como Claude o GPT) y tu código fuente. Le da a la IA la capacidad de "entender" la estructura profunda de tus clases, dependencias Maven/Gradle y la magia de las anotaciones de Spring, permitiéndole asistirte de manera mucho más precisa.

---

## 🌟 ¿Qué puedes hacer con esto?

Hemos dividido las capacidades en cuatro áreas clave para facilitar tu flujo de trabajo:

### 1. 🔬 Análisis de Código Profundo

No es solo leer texto; es entender Java.

* **Radiografía del Código:** Extrae clases, métodos y paquetes automáticamente.
* **Detector Spring:** Identifica al instante tus `@RestController`, `@Service`, `@Repository` y más.
* **Salud del Proyecto:** Revisa `pom.xml` o `build.gradle` y calcula métricas de calidad (complejidad, líneas de código).

### 2. 📂 Gestión Inteligente de Archivos

Olvídate de buscar manualmente.

* **Búsqueda Semántica:** Encuentra texto y contenido específico con coincidencias por línea.
* **Edición Segura:** Crea o edita archivos con validación de sintaxis Java incorporada (¡evita errores tontos!).
* **Configuración:** Lee y entiende archivos `.properties`, `.yml` y `.xml` sin despeinarse.

### 3. 📚 Documentación al Instante

* **Generador Automático:** Convierte tu código en documentación Markdown o HTML limpia.
* **API Docs:** Mapea tus endpoints REST automáticamente.
* **Javadoc:** Extrae comentarios y documentación técnica existente.

### 4. 🏗️ Visión de Arquitectura

* **Stack Tecnológico:** Detecta qué frameworks y librerías estás usando.
* **Mapa del Proyecto:** Genera un árbol jerárquico de directorios y componentes Spring.

---

## 🚀 Instalación y Puesta en Marcha

Tienes dos caminos para empezar. Te recomendamos encarecidamente usar **Docker** para mantener tu entorno limpio.

### Opción A: Vía Docker (Recomendada ⭐️)

La forma más rápida y aislada de correr el servidor.

1. **Clona el repo:**
```bash
git clone <repositorio-url>
cd cline-mcp-java-spring

```


2. **Levanta el servicio:**
```bash
docker-compose up --build -d

```


3. **¡Listo! Verifica que todo va bien:**
```bash
docker-compose logs -f

```



### Opción B: Instalación Manual (Python)

Si prefieres correrlo en "bare metal" o localmente:

1. **Instala las dependencias:**
```bash
pip install -r requirements.txt

```


2. **Enciende el servidor:**
```bash
python -m mcp_server.main

```



---

## 🧰 Caja de Herramientas (Toolbox)

Aquí tienes los comandos que puedes invocar. Cada uno está diseñado para una tarea específica en tu flujo de desarrollo.

### Análisis y Estructura

| Herramienta | Descripción | Ejemplo Rápido |
| --- | --- | --- |
| `analyze` | Tu navaja suiza. Analiza estructura, calidad o dependencias. | `await analyze("/ruta/App.java", "structure")` |
| `get_structure` | Obtén una vista de pájaro de todo el proyecto (carpetas y archivos). | `await get_structure("/workspace", depth=3)` |
| `detect_technologies` | ¿Qué usa este proyecto? (Hibernate, Kafka, JUnit...). | `await detect_technologies("/workspace")` |
| `get_function_signatures` | Extrae solo las firmas de métodos (ideal para interfaces). | `await get_function_signatures("/ruta/Svc.java")` |

### Archivos y Edición

| Herramienta | Descripción | Ejemplo Rápido |
| --- | --- | --- |
| `list_files` | Lista archivos filtrando por extensión (útil para proyectos grandes). | `await list_files("/workspace", "*.java")` |
| `read_file` | Lee un archivo interpretando su contexto Spring. | `await read_file("/ruta/Controller.java", True)` |
| `create_file` | Crea archivos nuevos validando que el Java sea correcto. | `await create_file("/ruta/NewDto.java", codigo)` |
| `search_files` | Grep inteligente: busca texto dentro de tus archivos. | `await search_files("/workspace", "TODO", "*.java")` |

### Documentación

| Herramienta | Descripción | Ejemplo Rápido |
| --- | --- | --- |
| `generate_docs` | Crea documentación leíble para humanos (MD/HTML). | `await generate_docs("/workspace", "markdown")` |
| `extract_comments` | Saca todo el Javadoc y comentarios del código. | `await extract_comments("/ruta/Api.java")` |

---

## 💡 Casos de Uso Reales

¿No estás seguro de cuándo usar qué? Aquí tienes algunos escenarios comunes:

### 1. "Aterrizando en un proyecto nuevo" 🛬

Acabas de clonar un repo legacy y necesitas entenderlo rápido.

```python
# 1. Mapa general
structure = await get_structure("/workspace/legacy-api")
# 2. ¿Qué tecnologías usa?
stack = await detect_technologies("/workspace/legacy-api")
# 3. Documentación de endpoints
docs = await generate_docs("/workspace/legacy-api", "markdown")

```

### 2. "Refactorizando con seguridad" 🛡️

Vas a tocar código crítico y necesitas contexto.

```python
# Analiza la clase antes de tocarla
analysis = await analyze("/workspace/PaymentService.java", "structure")
# Revisa las firmas de los métodos relacionados
signatures = await get_function_signatures("/workspace/PaymentRepository.java")

```

### 3. "Code Review Automatizado" 🤖

Quieres verificar la calidad antes de aprobar un PR.

```python
quality_report = await analyze("/workspace/feature-branch", "quality")

```

---

## 🔧 Configuración Avanzada

Si necesitas ajustar el comportamiento, usa estas variables de entorno o volúmenes en tu `docker-compose.yml`.

**Variables de Entorno:**

* `PYTHONPATH`: Ruta base (Default: `/app`).
* `LOG_LEVEL`: ¿Cuánto ruido quieres en los logs? (`DEBUG`, `INFO`, `WARNING`).

**Volúmenes Docker (Mapeos):**

* `/workspace`: **Importante.** Aquí es donde debes montar tu proyecto Java para que el servidor lo vea.
* `./mcp_server`: Si estás desarrollando el propio servidor MCP.

---

## 🚑 Solución de Problemas (Troubleshooting)

¿Algo no funciona? Revisa estos puntos comunes:

* **⚠️ El servidor no arranca:** Revisa tus volúmenes en Docker. ¿La ruta existe? Mira los logs con `docker-compose logs -f`.
* **⚠️ No detecta Spring Boot:** Asegúrate de que el proyecto tenga una clase con `@SpringBootApplication` y algún archivo `application.properties` o `.yml`.
* **⚠️ Permisos:** Si usas Linux/Mac, verifica que Docker tenga permiso de lectura sobre tu carpeta `/workspace`.

---

## 🔮 El Futuro (Roadmap)

Estamos trabajando en hacer esta herramienta aún mejor. Lo que viene:

* [ ] Soporte para **Quarkus** y **Micronaut**.
* [ ] Integración con bases de datos NoSQL.
* [ ] Generación de código más inteligente.
* [ ] Tests automáticos.

---

### 🤝 Contribuye

¿Tienes una idea? ¡Haz un Fork y mándanos un PR! Este proyecto es Open Source y nos encanta la colaboración.

**Licencia:** MIT License.


