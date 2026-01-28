# FuLLetLabs - Bot de Generación de Imágenes

Bot profesional de Discord para generación de imágenes por IA, modularizado mediante Cogs e integrado con ComfyUI.

## Características
- **Arquitectura Modular**: Basado en Cogs de Discord (Admin, Sesiones, Comandos).
- **Soporte Multi-Modelo**: Selección entre Flux (Schnell) y Z-Image (Turbo).
- **Feedback de Cola Dinámico**: Posición real (Pos: 3) y cuenta atrás (Queue: 3, 2, 1).
- **Métricas de Generación**: Reporte automático del tiempo de procesamiento.
- **Sesiones Privadas**: Creación y auto-borrado (30 min) de canales de usuario.
- **Seguridad**: Protección por ID de servidor, autorización por API Key y bloqueo de puertos.

## Cómo Funciona

El bot actúa como un cliente ligero que se conecta a ComfyUI vía HTTP. Esta arquitectura te permite:
- Ejecutar el bot en cualquier servidor económico (no requiere GPU)
- Usar ComfyUI localmente en tu propia máquina con GPU
- Rentar GPUs en la nube (RunPod, Vast.ai) y conectarte remotamente

```mermaid
graph LR
    A[Usuario Discord] -->|Comando /imagine| B[Bot Discord]
    B -->|Petición HTTP| C{Instancia ComfyUI}
    C -->|Opción 1| D[GPU Local<br/>127.0.0.1:8188]
    C -->|Opción 2| E[GPU en Nube<br/>RunPod/Vast.ai]
    C -->|Opción 3| F[Workspace<br/>Replicate/etc]
    D -->|Imagen Generada| B
    E -->|Imagen Generada| B
    F -->|Imagen Generada| B
    B -->|Enviar Imagen| A
    B <-->|Guardar Sesiones| G[(Base de Datos)]
    G -->|SQLite| H[Archivo Local]
    G -->|PostgreSQL| I[BD en Nube<br/>Aiven/Railway]
```

## Estructura
- `/modules/discord/bot.py`: Cargador principal y motor de trabajos.
- `/modules/discord/cogs/`: Funcionalidades núcleo separadas por módulos.
- `/modules/ai/`: Integración con API de ComfyUI y lógica de flujos.
- `/modules/queue_manager/`: Gestión de colas de prioridad.
- `/modules/utils/`: Base de datos (SQLAlchemy) y filtrado de imágenes.

## Requisitos Previos
Antes de ejecutar este bot, debes tener ComfyUI instalado y configurado:
1. Instala ComfyUI localmente o contrata un espacio de trabajo en la nube.
2. Instala los nodos GGUF en tu instalación de ComfyUI (requerido para cargar modelos).
3. Asegúrate de que ComfyUI sea accesible vía HTTP y hayas configurado autenticación por API Key.

## Configuración
1. Definir variables en `.env`:
   ```env
   DISCORD_TOKEN=tu_token
   ALLOWED_GUILD_ID=tu_id_de_servidor
   COMFY_URL=http://127.0.0.1:8188
   COMFY_API_KEY=tu_llave_secreta
   DATABASE_URL=postgresql://avnadmin:tu_contraseña@tu-proyecto.aivencloud.com:12345/defaultdb?sslmode=require
   ```
   Para `COMFY_URL`: Usa `http://127.0.0.1:8188` si ejecutas ComfyUI localmente. Si usas un espacio de trabajo en la nube o GPU rentada, reemplázala con la URL proporcionada (ej: `https://tu-espacio.ejemplo.com`).

   **Configuración de Base de Datos**:
   - Agrega `DATABASE_URL=` a tu archivo `.env`.
   - Déjala vacía para usar SQLite local (`database/bot_data.db`) - recomendado para desarrollo.
   - Para producción o despliegues en la nube, usa una base de datos externa con el siguiente formato:
     ```env
     DATABASE_URL=postgresql://usuario:contraseña@hostname:puerto/nombre_basededatos
     ```
   - Ejemplo (Aiven PostgreSQL):
     ```env
     DATABASE_URL=postgresql://avnadmin:tu_contraseña@tu-proyecto.aivencloud.com:12345/defaultdb?sslmode=require
     ```
   - Proveedores compatibles: Aiven, Railway, Render, Heroku, o cualquier servicio PostgreSQL/MySQL.
   - Importante: Asegúrate de que tu URL incluya parámetros SSL si tu proveedor los requiere (ej: `?sslmode=require`).

   **Configuración Multi-GPU (Opcional)**:
   Para usar múltiples GPUs, agrega estas variables a tu archivo `.env`:
   ```env
   # Lista de URLs de ComfyUI separadas por comas
   COMFY_URLS=http://gpu1:8188,http://gpu2:8188
   
   # VRAM en GB para cada GPU (separadas por comas, en el mismo orden)
   GPU_VRAM_GB=24,16
   
   # VRAM libre mínima requerida para aceptar trabajo (defecto: 4)
   MIN_FREE_VRAM=4
   ```

## Gestión Inteligente de VRAM

El bot incluye un programador inteligente que gestiona múltiples GPUs de forma eficiente:

```mermaid
graph TD
    A[Nueva Petición] --> B{Checar VRAM libre}
    B -->|"VRAM >= 4GB"| C[Procesar en GPU actual]
    B -->|"VRAM < 4GB"| D{Modelo grande?}
    D -->|"Modelo > VRAM libre"| E{Hay otra GPU?}
    D -->|"Modelo <= VRAM"| C
    E -->|Sí| F[Enviar a otra GPU]
    E -->|No| G[Encolar y esperar]
    C --> H[Actualizar VRAM usada]
    F --> H
```

2. Configuración de Flujos (`/flujos`):
   Para evitar errores, abre los archivos JSON en la carpeta `/flujos` y asegúrate de que los siguientes campos coincidan con los nombres de tus modelos en ComfyUI:
   - `unet_name`: Cambiar por el nombre de tu archivo de modelo de difusión.
   - `clip_name`: Cambiar por el nombre de tu archivo de modelo CLIP.
   O simplemente importa tus propios flujos exportándolos desde ComfyUI en formato API y reemplazando los archivos actuales.

3. Instalar dependencias: `pip install -r requirements.txt`
4. Iniciar aplicación: `python app.py`

## Comandos
- `/imagine [modelo] [prompt]`: Generar imagen con el modelo seleccionado.
- `/edit [prompt] [imagen]`: Editar imágenes (optimizado solo para Flux).
- `!sync`: (Admin) Sincronizar comandos slash en #admin-tools.
- `!clearall`: (Admin) Limpiar caché de comandos global y local.

## Buenas Prácticas de Seguridad
Sigue estas recomendaciones para proteger tu despliegue:

1. **Protección de Variables de Entorno**:
   - Nunca compartas tu `DISCORD_TOKEN` o `COMFY_API_KEY` públicamente.
   - Regenera los tokens inmediatamente si se exponen accidentalmente.

2. **Restricción de Servidor**:
   - Usa `ALLOWED_GUILD_ID` para restringir el bot a tu servidor específico de Discord.
   - Evita ejecutar el bot en servidores públicos o no confiables.

3. **Seguridad de ComfyUI**:
   - Si ejecutas ComfyUI localmente, no expongas el puerto 8188 a internet sin reglas de firewall adecuadas.
   - Siempre usa un `COMFY_API_KEY` fuerte para autenticación.
   - Si usas un espacio de trabajo en la nube, asegúrate de que requiera autenticación y use HTTPS.

4. **Seguridad de la Base de Datos**:
   - La carpeta `database/` está excluida de Git por defecto. Mantenla privada.
   - Respalda regularmente tu base de datos si guardas información importante de usuarios.

5. **Dependencias**:
   - Mantén las dependencias actualizadas con `pip install --upgrade -r requirements.txt` para parchear vulnerabilidades de seguridad.
