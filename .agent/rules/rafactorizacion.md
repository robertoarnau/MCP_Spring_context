---
trigger: always_on
---

## 5. Workflow de Refactorización y Cambios (Estricto)

### Principio de "Baby Steps"
- **Prohibido:** No realices refactorizaciones masivas en múltiples archivos simultáneamente.
- **Permitido:** Identifica la unidad de código más pequeña e independiente (una función, una clase pequeña) y refactoriza SOLO eso.

### Ciclo de Ejecución (Loop)
Para cada solicitud de refactorización (DRY, SOLID, etc.), debes seguir estrictamente este bucle:

1.  **Análisis:** Identifica el próximo cambio atómico necesario.
2.  **Modificación:** Aplica el cambio en el código (respetando POO e Inyección de Dependencias).
3.  **Verificación:** Genera o ejecuta el comando de test ESPECÍFICO para ese cambio (ej. `pytest tests/test_unitario_concreto.py`).
4.  **Validación:**
    * Si el test PASA: Confirma el cambio y procede al siguiente paso.
    * Si el test FALLA: **DETENTE**. No sigas refactorizando. Corrige el error inmediatamente antes de tocar cualquier otra línea de código.

### Comandos de Test
- No ejecutes la suite completa (`pytest`) si solo cambiaste una clase. Usa `pytest -k "NombreDeLaClase"` o apunta al archivo específico para iterar rápido.