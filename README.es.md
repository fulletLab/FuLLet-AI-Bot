# FuLLetLabs - Bot de Generación de Imágenes

Bot profesional de Discord para generación de imágenes por IA, modularizado mediante Cogs e integrado con ComfyUI. Esta versión incluye Fusión de Flujos (Batching Real) de alta eficiencia y escalado Multi-GPU autónomo.

## Nuevas Características de Alta Eficiencia
- **Fusión de Flujos (Batching Real)**: Utiliza el nodo personalizado `CLIPTextEncodeBatch` para procesar hasta 4 prompts en un solo paso del sampler.
- **Escalado Multi-GPU**: Crea automáticamente un trabajador por cada URL de GPU definida en la configuración.
- **Justicia de Usuario**: Implementa un límite de 2 trabajos activos por usuario y priorización equitativa en cada lote.
- **Control de VRAM**: Variable `MAX_BATCH_SIZE` configurable para garantizar estabilidad en tarjetas de 8GB.
- **Persistencia Mejorada**: Recuperación de canales por nombre si el registro en la base de datos no existe tras un reinicio.

## Características
- **Arquitectura Modular**: Basado en Cogs de Discord (Admin, Sesiones, Comandos).
- **Soporte Multi-Modelo**: Selección fluida entre Flux (Schnell) y Z-Image (Turbo).
- **Feedback de Cola Dinámico**: Seguimiento de posición y cuenta atrás de generación en tiempo real.
- **Métricas de Generación**: Reporte automático del tiempo de procesamiento por imagen.
- **Sesiones Privadas**: Gestión automática de canales privados dedicados para cada usuario.
- **Seguridad**: Protección por ID de servidor y autorización por API Key.

## Cómo Funciona

El bot utiliza un motor multi-trabajador que se conecta a una o varias instancias de ComfyUI vía HTTP. Actúa como un cliente ligero que gestiona la cola y la construcción dinámica de flujos.

```mermaid
graph TD
    A[Usuarios Discord] -->|Prompts| B[QueueManager]
    B -->|Filtro de Justicia| C{Pool de Trabajadores}
    C -->|Worker 1| D[GPU 1: Lote 1]
    C -->|Worker N| E[GPU N: Lote N]
    D -->|Real Batching| F[Instancia ComfyUI]
    E -->|Real Batching| F
    F -->|Imágenes Generadas| G[Distribución de Resultados]
    G -->|Mensaje Directo| A
```

Flexibilidad de la arquitectura:
- Ejecuta el bot en cualquier servidor (no requiere GPU para el proceso del bot).
- Conecta GPUs locales o proveedores en la nube (RunPod, Vast.ai, Lambda).
- Escala el sistema simplemente añadiendo más URLs a la configuración.

## Estructura
- `/modules/discord/bot.py`: Cargador principal y motor de trabajadores.
- `/modules/discord/cogs/`: Funcionalidades núcleo (Admin, Sesiones, Comandos).
- `/modules/ai/`: Integración con API de ComfyUI y construcción dinámica de flujos.
- `/modules/queue_manager/`: Cola de prioridad, cumplimiento de justicia y trabajadores paralelos.
- `/modules/utils/`: Base de datos (SQLAlchemy) y filtrado de imágenes.
- `/comfy_custom_nodes/`: Nodos personalizados necesarios para el servidor ComfyUI.

## Requisitos Previos
1. **ComfyUI**: Debe estar instalado y accesible vía HTTP.
2. **Nodos GGUF**: Necesarios para cargar los modelos Flux pesados.
3. **Nodo FuLLet**: Copia `comfy_custom_nodes/batch_conditioning.py` a tu carpeta `ComfyUI/custom_nodes/` y reinicia.
4. **Base de Datos**: SQLite (por defecto) o cualquier servicio PostgreSQL.

## Configuración
Define tus variables de entorno en el archivo `.env`:
```env
DISCORD_TOKEN=tu_token
ALLOWED_GUILD_ID=tu_id_de_servidor
COMFY_URLS=http://gpu1:8188,http://gpu2:8188
COMFY_API_KEY=tu_llave_secreta
DATABASE_URL=postgresql://usuario:pass@host:puerto/db
MAX_BATCH_SIZE=2
```

### Configuración Detallada

**1. Configuración de GPUs**:
- `COMFY_URLS`: Lista separada por comas de tus servidores ComfyUI. El bot inicia un trabajador paralelo por cada URL.
- `MAX_BATCH_SIZE`: Número de imágenes por lote.
    - 2: Recomendado para tarjetas de 8GB VRAM (Flux).
    - 4: Recomendado para tarjetas de 24GB+ VRAM.

**2. Configuración de Base de Datos**:
- `DATABASE_URL`: Dejar vacío para usar SQLite local (`database/bot_data.db`).
- Formato para PostgreSQL (Aiven, Railway, etc.):
  `postgresql://usuario:contraseña@hostname:puerto/nombre_bd?sslmode=require`

**3. Configuración de Flujos (`/flujos`)**:
El bot construye los flujos dinámicamente, pero debes asegurar que los nombres de los modelos en tu servidor coincidan con las plantillas `.json`:
- `unet_name`: Tu archivo de modelo GGUF.
- `clip_name`: Tu archivo CLIP GGUF.

## Comandos
- `/imagine [modelo] [prompt]`: Generar imagen con el modelo seleccionado.
- `/edit [prompt] [imagen]`: Editar imágenes (optimizado solo para Flux).
- `!sync`: (Admin) Sincronizar comandos slash.
- `!clearall`: (Admin) Limpiar caché de comandos.
- `!getid`: (Admin) Obtener el ID del servidor actual.

## Buenas Prácticas de Seguridad
1. **Protección de Tokens**: Nunca compartas tus llaves API públicamente.
2. **Restricción de Servidor**: Usa siempre `ALLOWED_GUILD_ID`.
3. **Firewall**: Protege la API de ComfyUI con API Key y preferiblemente mediante un túnel seguro.
4. **Privacidad de Datos**: La carpeta `database/` está excluida de Git. Mantenla privada.
