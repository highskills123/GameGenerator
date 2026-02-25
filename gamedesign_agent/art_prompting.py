"""
art_prompting.py – Art prompt generator for Stable Diffusion / DALL-E.

Generates high-quality text prompts (fully offline by default).

Optional backends:
  • "auto1111" – submits the prompt to a running AUTOMATIC1111
                  stable-diffusion-webui instance via its REST API.
  • "diffusers" – runs a local 🤗 diffusers pipeline
                  (requires GPU + user-supplied model weights).

NOTE: You must supply your own model weights for local SD.
      Do NOT add large model files to this repository.
"""

from __future__ import annotations

import base64
import os
import random
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import config


# ---------------------------------------------------------------------------
# Prompt component pools
# ---------------------------------------------------------------------------

_STYLE_KEYWORDS: Dict[str, List[str]] = {
    "fantasy": [
        "fantasy art", "epic fantasy", "high fantasy illustration",
        "dungeons and dragons style", "artstation trending", "concept art",
    ],
    "sci-fi": [
        "science fiction concept art", "cyberpunk", "space opera", "futuristic",
        "hard sci-fi illustration", "artstation trending",
    ],
    "horror": [
        "dark horror art", "gothic horror", "creepy atmosphere",
        "lovecraftian horror", "dark fantasy", "eerie",
    ],
    "cartoon": [
        "cartoon style", "cel-shaded", "stylized", "colorful",
        "studio ghibli inspired", "2D game art",
    ],
    "realistic": [
        "photorealistic", "ultra detailed", "8K", "cinematic lighting",
        "hyperrealism", "unreal engine render",
    ],
    "pixel": [
        "pixel art", "16-bit style", "retro game art", "isometric pixel art",
        "SNES style", "indie game pixel art",
    ],
}

_QUALITY_TAGS = [
    "masterpiece", "best quality", "highly detailed",
    "sharp focus", "intricate details",
]

_NEGATIVE_PROMPT_BASE = (
    "blurry, low quality, watermark, text, signature, ugly, deformed, "
    "bad anatomy, extra limbs, worst quality, jpeg artifacts"
)

_SCENE_DESCRIPTORS: Dict[str, List[str]] = {
    "dungeon": [
        "stone dungeon corridor", "torch-lit hallway", "ancient underground chamber",
        "mossy dungeon walls", "treasure room filled with gold",
    ],
    "forest": [
        "ancient enchanted forest", "dense woodland at dusk",
        "mystical forest clearing", "overgrown forest ruins",
    ],
    "castle": [
        "medieval castle exterior", "grand throne room",
        "crumbling castle ramparts", "dark castle courtyard at night",
    ],
    "city": [
        "bustling fantasy marketplace", "cobblestone city street at night",
        "steampunk city skyline", "neon-lit cyberpunk alley",
    ],
    "character": [
        "heroic warrior portrait", "mysterious hooded mage",
        "cunning rogue in shadows", "armored paladin standing tall",
    ],
    "creature": [
        "fearsome dragon breathing fire", "undead skeleton warrior",
        "giant spider in a web-filled cave", "spectral ghost haunting a hallway",
    ],
    "item": [
        "legendary magic sword glowing blue", "ancient spell tome with glowing runes",
        "enchanted amulet on a velvet cushion", "mysterious potion bottle",
    ],
    "landscape": [
        "sweeping mountain vista at sunrise", "volcanic wasteland under a red sky",
        "frozen tundra with northern lights", "desert ruins at golden hour",
    ],
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ArtPrompt:
    positive: str
    negative: str
    style: str
    scene_type: str
    seed: int
    metadata: Dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.positive

    def to_dict(self) -> dict:
        return {
            "positive": self.positive,
            "negative": self.negative,
            "style": self.style,
            "scene_type": self.scene_type,
            "seed": self.seed,
            "metadata": self.metadata,
        }


@dataclass
class GeneratedImage:
    prompt: ArtPrompt
    image_path: Optional[str] = None
    image_b64: Optional[str] = None  # base64-encoded PNG
    backend_used: str = "none"

    def to_dict(self) -> dict:
        return {
            "backend_used": self.backend_used,
            "image_path": self.image_path,
            "prompt": self.prompt.to_dict(),
        }


# ---------------------------------------------------------------------------
# ArtPromptGenerator
# ---------------------------------------------------------------------------

class ArtPromptGenerator:
    """
    Generates Stable Diffusion / DALL-E style text prompts.

    Parameters
    ----------
    art_backend : str
        Overrides ``config.ART_BACKEND``.
        ``"none"`` – generate prompt text only (default, fully offline).
        ``"auto1111"`` – send to AUTOMATIC1111 webui API.
        ``"diffusers"`` – use local 🤗 diffusers pipeline.
    """

    def __init__(self, art_backend: Optional[str] = None) -> None:
        self._backend = (art_backend or config.ART_BACKEND).lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_prompt(
        self,
        scene_type: str = "dungeon",
        style: str = "fantasy",
        description: Optional[str] = None,
        extra_tags: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> ArtPrompt:
        """
        Build a detailed art prompt.

        Parameters
        ----------
        scene_type : str
            Category hint; one of: dungeon, forest, castle, city, character,
            creature, item, landscape (or any free text).
        style : str
            Visual style: fantasy, sci-fi, horror, cartoon, realistic, pixel.
        description : str, optional
            User-supplied free-text description appended after generated tags.
        extra_tags : list[str], optional
            Additional comma-separated tags to append.
        seed : int, optional
            RNG seed for reproducible prompts.
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        rng = random.Random(seed)

        style_pool = _STYLE_KEYWORDS.get(style.lower(), _STYLE_KEYWORDS["fantasy"])
        scene_pool = _SCENE_DESCRIPTORS.get(scene_type.lower(), [scene_type])

        style_tag = rng.choice(style_pool)
        scene_tag = rng.choice(scene_pool)
        quality_tags = rng.sample(_QUALITY_TAGS, k=min(3, len(_QUALITY_TAGS)))

        parts: List[str] = [scene_tag, style_tag] + quality_tags
        if description:
            parts.insert(0, description)
        if extra_tags:
            parts.extend(extra_tags)

        positive = ", ".join(parts)
        negative = _NEGATIVE_PROMPT_BASE

        return ArtPrompt(
            positive=positive,
            negative=negative,
            style=style,
            scene_type=scene_type,
            seed=seed,
            metadata={
                "style_tag": style_tag,
                "scene_tag": scene_tag,
                "quality_tags": quality_tags,
            },
        )

    def generate_character_prompt(
        self,
        character_class: str,
        race: str = "human",
        style: str = "fantasy",
        traits: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> ArtPrompt:
        """Convenience wrapper for character portrait prompts."""
        desc = f"{race} {character_class}"
        if traits:
            desc += ", " + ", ".join(traits)
        return self.generate_prompt(
            scene_type="character",
            style=style,
            description=desc,
            seed=seed,
        )

    def generate_environment_prompt(
        self,
        biome: str,
        time_of_day: str = "day",
        weather: str = "clear",
        style: str = "fantasy",
        seed: Optional[int] = None,
    ) -> ArtPrompt:
        """Convenience wrapper for environment / landscape prompts."""
        desc = f"{biome} environment, {time_of_day}, {weather} weather"
        scene = biome if biome in _SCENE_DESCRIPTORS else "landscape"
        return self.generate_prompt(
            scene_type=scene,
            style=style,
            description=desc,
            seed=seed,
        )

    def list_styles(self) -> List[str]:
        return list(_STYLE_KEYWORDS.keys())

    def list_scene_types(self) -> List[str]:
        return list(_SCENE_DESCRIPTORS.keys())

    # ------------------------------------------------------------------
    # Optional image generation
    # ------------------------------------------------------------------

    def generate_image(
        self,
        prompt: ArtPrompt,
        output_path: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
    ) -> GeneratedImage:
        """
        Optionally submit the prompt to a configured image backend.

        When ``art_backend == "none"`` (default) this method returns a
        :class:`GeneratedImage` with no image data – only the prompt.
        """
        if self._backend == "none":
            return GeneratedImage(prompt=prompt, backend_used="none")
        elif self._backend == "auto1111":
            return self._auto1111_generate(prompt, output_path, width, height, steps)
        elif self._backend == "diffusers":
            return self._diffusers_generate(prompt, output_path, width, height, steps)
        else:
            raise ValueError(f"Unknown art backend: {self._backend!r}")

    # ------------------------------------------------------------------
    # AUTOMATIC1111 adapter (free, local)
    # ------------------------------------------------------------------

    def _auto1111_generate(
        self,
        prompt: ArtPrompt,
        output_path: Optional[str],
        width: int,
        height: int,
        steps: int,
    ) -> GeneratedImage:
        try:
            import requests  # type: ignore
        except ImportError as e:
            raise ImportError("Install 'requests' to use the auto1111 backend.") from e

        payload = {
            "prompt": prompt.positive,
            "negative_prompt": prompt.negative,
            "seed": prompt.seed,
            "width": width,
            "height": height,
            "steps": steps,
            "sampler_name": "Euler a",
            "cfg_scale": 7,
        }
        url = f"{config.AUTO1111_URL}/sdapi/v1/txt2img"
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        images: List[str] = data.get("images", [])
        if not images:
            return GeneratedImage(prompt=prompt, backend_used="auto1111")

        image_b64 = images[0]
        saved_path: Optional[str] = None
        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
            saved_path = output_path
        elif config.OUTPUT_DIR:
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            fname = f"sd_{prompt.seed}_{prompt.scene_type}.png"
            saved_path = os.path.join(config.OUTPUT_DIR, fname)
            with open(saved_path, "wb") as f:
                f.write(base64.b64decode(image_b64))

        return GeneratedImage(
            prompt=prompt,
            image_path=saved_path,
            image_b64=image_b64,
            backend_used="auto1111",
        )

    # ------------------------------------------------------------------
    # 🤗 diffusers adapter (free, local GPU)
    # ------------------------------------------------------------------

    def _diffusers_generate(
        self,
        prompt: ArtPrompt,
        output_path: Optional[str],
        width: int,
        height: int,
        steps: int,
    ) -> GeneratedImage:
        try:
            import torch  # type: ignore
            from diffusers import StableDiffusionPipeline  # type: ignore
        except ImportError as e:
            raise ImportError(
                "Install 'torch' and 'diffusers' to use the diffusers backend.\n"
                "  pip install torch diffusers transformers accelerate\n"
                "You must also supply your own model weights – do NOT commit "
                "large model files to this repository."
            ) from e

        pipe = StableDiffusionPipeline.from_pretrained(
            config.DIFFUSERS_MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = pipe.to(device)

        generator = torch.Generator(device=device).manual_seed(prompt.seed)
        result = pipe(
            prompt.positive,
            negative_prompt=prompt.negative,
            width=width,
            height=height,
            num_inference_steps=steps,
            generator=generator,
        )
        image = result.images[0]

        saved_path: Optional[str] = output_path
        if saved_path is None and config.OUTPUT_DIR:
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            fname = f"sd_{prompt.seed}_{prompt.scene_type}.png"
            saved_path = os.path.join(config.OUTPUT_DIR, fname)
        if saved_path:
            os.makedirs(os.path.dirname(saved_path) or ".", exist_ok=True)
            image.save(saved_path)

        return GeneratedImage(
            prompt=prompt,
            image_path=saved_path,
            backend_used="diffusers",
        )
