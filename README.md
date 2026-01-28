# FuLLetLabs - Image Generation Bot

Professional Discord bot for AI image generation, modularized using Cogs and integrated with ComfyUI.

## Features
- **Modular Architecture**: Built with Discord Cogs (Admin, Sessions, ImageCommands).
- **Multi-Model Support**: Selection between Flux (Schnell) and Z-Image (Turbo).
- **Dynamic Queue Feedback**: Real-time position (e.g., Pos: 3) and countdown (Queue: 3, 2, 1).
- **Generation Metrics**: Automatic reporting of processing time per image.
- **Private Sessions**: Automatic creation and auto-deletion (30 min) of user channels.
- **Security**: Server ID protection, API Key authorization, and local port binding.

## How It Works

The bot acts as a lightweight client that connects to ComfyUI via HTTP. This architecture allows you to:
- Run the bot on any cheap server (no GPU required)
- Use ComfyUI locally on your own machine with GPU
- Rent cloud GPUs (RunPod, Vast.ai) and connect remotely

```mermaid
graph LR
    A[Discord User] -->|/imagine command| B[Discord Bot]
    B -->|HTTP Request| C{ComfyUI Instance}
    C -->|Option 1| D[Local GPU<br/>127.0.0.1:8188]
    C -->|Option 2| E[Cloud GPU<br/>RunPod/Vast.ai]
    C -->|Option 3| F[Workspace<br/>Replicate/etc]
    D -->|Generated Image| B
    E -->|Generated Image| B
    F -->|Generated Image| B
    B -->|Send Image| A
    B <-->|Store Sessions| G[(Database)]
    G -->|SQLite| H[Local File]
    G -->|PostgreSQL| I[Cloud DB<br/>Aiven/Railway]
```

## Structure
- `/modules/discord/bot.py`: Main bot loader and worker engine.
- `/modules/discord/cogs/`: Core features (Admin, Sessions, Commands).
- `/modules/ai/`: ComfyUI API integration and workflow logic.
- `/modules/queue_manager/`: Priority queue and job management.
- `/modules/utils/`: Database (SQLAlchemy) and image sanitization.

## Prerequisites
Before running this bot, you must have ComfyUI installed and configured:
1. Install ComfyUI locally or subscribe to a cloud workspace service.
2. Install the GGUF nodes in your ComfyUI installation (required for model loading).
3. Ensure ComfyUI is accessible via HTTP and you have configured API key authentication.

## Configuration
1. Define environment variables in `.env`:
   ```env
   DISCORD_TOKEN=your_token
   ALLOWED_GUILD_ID=your_server_id
   COMFY_URL=http://127.0.0.1:8188
   COMFY_API_KEY=your_secret_key
   ```
   For `COMFY_URL`: Use `http://127.0.0.1:8188` if running ComfyUI locally. If using a cloud workspace or rented GPU, replace with the provided URL (e.g., `https://your-workspace.example.com`).
   
   **Database Configuration**:
   - Add `DATABASE_URL=` to your `.env` file.
   - Leave it empty to use local SQLite (`database/bot_data.db`) - recommended for development.
   - For production or cloud deployments, use an external database with the following format:
     ```env
     DATABASE_URL=postgresql://username:password@hostname:port/database_name
     ```
   - Example (Aiven PostgreSQL):
     ```env
     DATABASE_URL=postgresql://avnadmin:your_password@your-project.aivencloud.com:12345/defaultdb?sslmode=require
     ```
   - Supported providers: Aiven, Railway, Render, Heroku, or any PostgreSQL/MySQL service.
   - Important: Ensure your database URL includes SSL parameters if required by your provider (e.g., `?sslmode=require`).
   
2. Workflow Setup (`/flujos`):
   To avoid errors, open the JSON files in the `/flujos` directory and ensure the following fields match your ComfyUI model names:
   - `unet_name`: Rename to your specific diffusion model filename.
   - `clip_name`: Rename to your specific CLIP model filename.
   Alternatively, you can simply import your own flows by exporting them from ComfyUI in API format and replacing these files.

3. Install dependencies: `pip install -r requirements.txt`
4. Launch application: `python app.py`

## Commands
- `/imagine [model] [prompt]`: Generate image with selected model.
- `/edit [prompt] [image]`: Edit images (Flux-only optimized).
- `!sync`: (Admin) Synchronize slash commands in #admin-tools.
- `!clearall`: (Admin) Clear global and local command cache.

## Security Best Practices
Follow these recommendations to protect your deployment:

1. **Environment Variables Protection**:
   - Never share your `DISCORD_TOKEN` or `COMFY_API_KEY` publicly.
   - Regenerate tokens immediately if accidentally exposed.

2. **Server Restriction**:
   - Use `ALLOWED_GUILD_ID` to restrict the bot to your specific Discord server.
   - Avoid running the bot on public or untrusted servers.

3. **ComfyUI Security**:
   - If running ComfyUI locally, do not expose port 8188 to the internet without proper firewall rules.
   - Always use a strong `COMFY_API_KEY` for authentication.
   - If using a cloud workspace, ensure it requires authentication and uses HTTPS.

4. **Database Security**:
   - The `database/` folder is excluded from Git by default. Keep it private.
   - Regularly backup your database if storing important user data.

5. **Dependencies**:
   - Keep dependencies updated with `pip install --upgrade -r requirements.txt` to patch security vulnerabilities.

---

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
