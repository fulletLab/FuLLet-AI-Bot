# FuLLetLabs - Image Generation Bot

Professional Discord bot for AI image generation, modularized using Cogs and integrated with ComfyUI. This version features high-efficiency Workflow Merging (Real Batching) and autonomous Multi-GPU scaling.

## New High-Efficiency Features
- **Workflow Merging (Real Batching)**: Uses the custom `CLIPTextEncodeBatch` node to process up to 4 prompts in a single sampler pass.
- **Multi-GPU Scaling**: Automatically spawns one worker loop per GPU URL defined in configuration.
- **User Fairness**: Implements a 2-job limit per user and round-robin prioritization within batches.
- **VRAM Tuning**: Safety-first batching with configurable `MAX_BATCH_SIZE` (optimized for 8GB cards).
- **Persistence**: Enhanced session recovery via name-based channel search if the database record is missing.

## Features
- **Modular Architecture**: Built with Discord Cogs (Admin, Sessions, ImageCommands).
- **Multi-Model Support**: Seamlessly switch between Flux (Schnell) and Z-Image (Turbo).
- **Dynamic Queue Feedback**: Real-time position tracking and generation countdowns.
- **Generation Metrics**: Automatic reporting of processing time per image.
- **Private Sessions**: Automatic creation and auto-management of dedicated user channels.
- **Security**: Server ID protection, API Key authorization, and local port binding.

## How It Works

The bot operates a multi-worker engine that connects to one or more ComfyUI instances via HTTP. It acts as a lightweight client that manages the queue and dynamic workflow construction.

```mermaid
graph TD
    A[Discord Users] -->|Prompts| B[QueueManager]
    B -->|Fairness Filter| C{Worker Pool}
    C -->|Worker 1| D[GPU 1: Batch 1]
    C -->|Worker N| E[GPU N: Batch N]
    D -->|Real Batching| F[ComfyUI Instance]
    E -->|Real Batching| F
    F -->|Generated Images| G[Result Distribution]
    G -->|Direct Message| A
```

Architecture flexibility:
- Run the bot on any server (GPU not required for the bot itself).
- Connect to local GPUs or remote cloud providers (RunPod, Vast.ai, Lambda).
- Scale by adding more URLs to the configuration.

## Structure
- `/modules/discord/bot.py`: Main bot loader and worker engine.
- `/modules/discord/cogs/`: Core features (Admin, Sessions, Commands).
- `/modules/ai/`: ComfyUI API integration and dynamic workflow construction.
- `/modules/queue_manager/`: Priority queue, fairness enforcement, and parallel workers.
- `/modules/utils/`: Database (SQLAlchemy) and image sanitization.
- `/comfy_custom_nodes/`: Required custom nodes for the ComfyUI server.

## Prerequisites
1. **ComfyUI**: Must be installed and accessible via HTTP.
2. **GGUF Nodes**: Required for loading Flux models.
3. **FuLLet Custom Node**: Copy `comfy_custom_nodes/batch_conditioning.py` to your `ComfyUI/custom_nodes/` folder and restart.
4. **Database**: SQLite (default) or any PostgreSQL service.

## Configuration
Define your environment variables in `.env`:
```env
DISCORD_TOKEN=your_token
ALLOWED_GUILD_ID=your_server_id
COMFY_URLS=http://gpu1:8188,http://gpu2:8188
COMFY_API_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
MAX_BATCH_SIZE=2
```

### Detailed Setup

**1. GPU Configuration**:
- `COMFY_URLS`: Comma-separated list of your ComfyUI endpoints. The bot starts one parallel worker per URL.
- `MAX_BATCH_SIZE`: Number of images per batch. 
    - 2: Recommended for 8GB VRAM cards (Flux).
    - 4: Recommended for 24GB+ VRAM cards.

**2. Database Configuration**:
- `DATABASE_URL`: Leave empty to use local SQLite (`database/bot_data.db`).
- Format for PostgreSQL (Aiven, Railway, etc.):
  `postgresql://username:password@hostname:port/database_name?sslmode=require`

**3. Workflow Setup (`/flujos`)**:
The bot builds workflows dynamically, but you must ensure the model names in your ComfyUI server match the ones in the `.json` templates:
- `unet_name`: Your GGUF model filename.
- `clip_name`: Your CLIP GGUF filename.

## Commands
- `/imagine [model] [prompt]`: Generate image with selected model.
- `/edit [prompt] [image]`: Edit images (Flux-only optimized).
- `!sync`: (Admin) Synchronize slash commands.
- `!clearall`: (Admin) Clear command cache.
- `!getid`: (Admin) Get current Server ID.

## Security Best Practices
1. **Token Protection**: Never share your secrets publicly.
2. **Server Restriction**: Use `ALLOWED_GUILD_ID` to restrict bot access.
3. **Firewall**: Ensure ComfyUI API is protected by API Key and preferably used over a secure tunnel.
4. **Data Privacy**: The `database/` folder is git-ignored by default. Keep it private.
