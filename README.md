# FuLLetLabs - Image Generation Bot

Professional Discord bot for AI image generation, modularized using Cogs and integrated with ComfyUI. This version includes high-performance Workflow Merging (Real Batching) and Multi-GPU scaling.

## New High-Performance Features
- **Workflow Merging**: Efficient real batching using custom `CLIPTextEncodeBatch` nodes to process multiple prompts in a single sampler pass.
- **Multi-GPU Scaling**: Automatic worker spawning (one per GPU) for parallel batch processing across different servers.
- **User Fairness**: 2-job limit per user and round-robin prioritization within batches to ensure fair resource distribution.
- **VRAM Tuning**: Configurable `MAX_BATCH_SIZE` for stability on 8GB cards and automatic batch size synchronization.
- **Enhanced Persistence**: Name-based channel retrieval ensuring session continuity even if database records are missing.

## Features
- **Modular Architecture**: Built with Discord Cogs (Admin, Sessions, ImageCommands).
- **Multi-Model Support**: Selection between Flux (GGUF) and Z-Image (Turbo).
- **Dynamic Queue Feedback**: Real-time position tracking and generation countdowns.
- **Generation Metrics**: Automatic reporting of processing time per image.
- **Private Sessions**: Dedicated channels for each user with automated persistence.
- **Security**: Server ID protection, API Key authorization, and local port binding.

## How It Works

The bot operates a multi-worker engine that connects to one or more ComfyUI instances via HTTP. It optimizes processing by grouping individual prompts into dynamic batches.

Technical highlights:
- **CLIP Text Encode (Batch)**: Merges up to 4 user prompts into a single conditioning tensor. This allows the GPU to perform a single sampler pass for the entire batch, saving 60-70% VRAM compared to individual samplers.
- **Dynamic Worker Balancing**: Each ComfyUI URL in the configuration spawns a dedicated worker, maximizing hardware utilization across multiple local or remote GPUs.
- **Fairness Enforcement**: The `QueueManager` uses a round-robin strategy to fill batches, ensuring that no single user can monopolize the GPU.

```mermaid
graph TD
    U[Users] -->|Prompts| QM[QueueManager]
    QM -->|Dynamic Batches| W[Worker Pool]
    W -->|Merge Prompts| CTE["CLIP Text Encode (Batch)"]
    CTE -->|Single Pass Conditioning| KSA[SamplerCustomAdvanced]
    KSA -->|GPU Inference| VAE[VAEDecode]
    VAE -->|Batch Image Tensors| SI[SaveImage]
    SI -->|Break Batch| RD[Result Distribution]
    RD -->|Image A| UA[User A]
    RD -->|Image B| UB[User B]
```

Architecture flexibility:
- Run the bot on any server (no GPU required for the bot itself).
- Connect to local GPUs or remote cloud providers (RunPod, Vast.ai).
- Scale by adding more URLs to the configuration.

## Structure
- `/modules/discord/bot.py`: Main bot loader and worker engine.
- `/modules/discord/cogs/`: Core features separated by Cogs (Admin, Sessions, Commands).
- `/modules/ai/`: ComfyUI API integration and dynamic workflow builder.
- `/modules/queue_manager/`: Priority queue, fairness enforcement, and parallel loops.
- `/modules/utils/`: Database (SQLAlchemy) and image sanitization.
- `/comfy_custom_nodes/`: Required custom nodes for the ComfyUI server.

## Prerequisites
1. **ComfyUI**: Installed and accessible via HTTP.
2. **GGUF Nodes**: Required for loading Flux GGUF models.
3. **FuLLet Custom Nodes**: You MUST copy the entire `comfy_custom_nodes/` folder to your `ComfyUI/custom_nodes/` directory and restart the server.
4. **Database**: SQLite (default) or any PostgreSQL service.
5. **Python 3.10+**: And dependencies from `requirements.txt`.

## Configuration
Define your environment variables in `.env`:
```env
DISCORD_TOKEN=your_token
ALLOWED_GUILD_ID=your_server_id
COMFY_URLS=http://gpu1:8188,http://gpu2:8188
COMFY_API_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
MAX_BATCH_SIZE=2
```

### Detailed Setup

**1. GPU Configuration**:
- `COMFY_URLS`: Comma-separated list of your ComfyUI endpoints. The bot starts one parallel worker per URL.
- `MAX_BATCH_SIZE`: Number of images per batch. 
    - **2**: Recommended for 8GB VRAM cards (Flux).
    - **4**: Recommended for 24GB+ VRAM cards.

**2. Database Configuration**:
- `DATABASE_URL`: Leave empty to use local SQLite (`database/bot_data.db`).
- Format for PostgreSQL: `postgresql://username:password@hostname:port/database_name?sslmode=require`.
- Supports Aiven, Railway, Render, and Heroku.

**3. Workflow Setup (`/flujos`)**:
The bot builds workflows dynamically based on templates:
- `flux_image.json`: Default Flux generate workflow.
- `z-image_imagine.json`: Turbo model workflow.
Ensure `unet_name` and `clip_name` in these files match your server's filename exactly.

**4. Remote Access (Ngrok/Cloud)**:
- If using Ngrok with Basic Auth, use `username:password` in `COMFY_API_KEY`.
- The bot includes `ngrok-skip-browser-warning` headers by default.

## Commands
- `/imagine [model] [prompt]`: Generate image with selected model.
- `/edit [prompt] [image]`: Edit images using Flux.
- `!sync`: (Admin) Synchronize slash commands.
- `!clearall`: (Admin) Clear command cache.
- `!getid`: (Admin) Get the current Server ID.

## Security Best Practices
1. **Token Protection**: Never share `.env` or secrets.
2. **Firewall**: Protect ComfyUI ports with API Key and restricted access.
3. **Session Privacy**: `database/` is excluded from git to protect user data.
4. **SSL**: Always use `sslmode=require` for cloud databases.

## Credits
The custom batching nodes included in this project are a modified version based on the original work by [laksjdjf](https://github.com/laksjdjf) in the [Batch-Condition-ComfyUI](https://github.com/laksjdjf/Batch-Condition-ComfyUI) repository. We acknowledge and appreciate their contribution to the ComfyUI community.
