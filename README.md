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
   DATABASE_URL=postgresql://avnadmin:tu_contraseña@tu-proyecto.aivencloud.com:12345/defaultdb?sslmode=require
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

   **Multi-GPU Configuration (Optional)**:
   To use multiple GPUs, add these variables to your `.env` file:
   ```env
   # Comma-separated list of ComfyUI URLs
   COMFY_URLS=http://gpu1:8188,http://gpu2:8188
   
   # Comma-separated VRAM size in GB for each GPU (must handle same order as URLs)
   GPU_VRAM_GB=24,16
   
   # Minimum free VRAM required to accept a job (default: 4)
   MIN_FREE_VRAM=4
   ```

## Smart VRAM Scheduling

The bot includes an intelligent scheduler that manages multiple GPUs efficiently:

```mermaid
graph TD
    A[New Request] --> B{Check Free VRAM}
    B -->|"VRAM >= 4GB"| C[Process on Current GPU]
    B -->|"VRAM < 4GB"| D{Large Model?}
    D -->|"Model > Free VRAM"| E{Other GPU Available?}
    D -->|"Model <= VRAM"| C
    E -->|Yes| F[Send to Other GPU]
    E -->|No| G[Queue and Wait]
    C --> H[Update Used VRAM]
    F --> H
```

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
