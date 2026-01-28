# FuLLetLabs - Image Generation Bot

Professional Discord bot for AI image generation, modularized using Cogs and integrated with ComfyUI.

## Features
- **Modular Architecture**: Built with Discord Cogs (Admin, Sessions, ImageCommands).
- **Multi-Model Support**: Selection between Flux (Schnell) and Z-Image (Turbo).
- **Dynamic Queue Feedback**: Real-time position (e.g., Pos: 3) and countdown (Queue: 3, 2, 1).
- **Generation Metrics**: Automatic reporting of processing time per image.
- **Private Sessions**: Automatic creation and auto-deletion (30 min) of user channels.
- **Security**: Server ID protection, API Key authorization, and local port binding.

## Structure
- `/modules/discord/bot.py`: Main bot loader and worker engine.
- `/modules/discord/cogs/`: Core features (Admin, Sessions, Commands).
- `/modules/ai/`: ComfyUI API integration and workflow logic.
- `/modules/queue_manager/`: Priority queue and job management.
- `/modules/utils/`: Database (SQLAlchemy) and image sanitization.

## Setup
1. Define environment variables in `.env`:
   ```env
   DISCORD_TOKEN=your_token
   ALLOWED_GUILD_ID=your_server_id
   COMFY_URL=http://your-ip:8188
   COMFY_API_KEY=your_secret_key
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Launch application: `python app.py`

## Commands
- `/imagine [model] [prompt]`: Generate image with selected model.
- `/edit [prompt] [image]`: Edit images (Flux-only optimized).
- `!sync`: (Admin) Synchronize slash commands in #admin-tools.
- `!clearall`: (Admin) Clear global and local command cache.

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

## Estructura
- `/modules/discord/bot.py`: Cargador principal y motor de trabajos.
- `/modules/discord/cogs/`: Funcionalidades núcleo separadas por módulos.
- `/modules/ai/`: Integración con API de ComfyUI y lógica de flujos.
- `/modules/queue_manager/`: Gestión de colas de prioridad.
- `/modules/utils/`: Base de datos (SQLAlchemy) y filtrado de imágenes.

## Configuración
1. Definir variables en `.env`:
   ```env
   DISCORD_TOKEN=tu_token
   ALLOWED_GUILD_ID=tu_id_de_servidor
   COMFY_URL=http://tu-ip:8188
   COMFY_API_KEY=tu_llave_secreta
   ```
2. Instalar dependencias: `pip install -r requirements.txt`
3. Iniciar aplicación: `python app.py`

## Comandos
- `/imagine [modelo] [prompt]`: Generar imagen con el modelo seleccionado.
- `/edit [prompt] [imagen]`: Editar imágenes (optimizado solo para Flux).
- `!sync`: (Admin) Sincronizar comandos slash en #admin-tools.
- `!clearall`: (Admin) Limpiar caché de comandos global y local.
