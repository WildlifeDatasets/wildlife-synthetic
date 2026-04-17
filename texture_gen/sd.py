from transformers import CLIPTextModel, CLIPTokenizer, logging
from diffusers import AutoencoderKL, UNet2DConditionModel, PNDMScheduler, DDIMScheduler
from diffusers.utils.import_utils import is_xformers_available
from PIL import Image
import matplotlib.pyplot as plt
import os
# suppress partial model loading warning
logging.set_verbosity_error()

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.cuda.amp import custom_bwd, custom_fwd
from pathlib import Path
import inspect

try:
    from huggingface_hub import snapshot_download
except Exception:
    snapshot_download = None


class SpecifyGradient(torch.autograd.Function):
    @staticmethod
    @custom_fwd
    def forward(ctx, input_tensor, gt_grad):
        ctx.save_for_backward(gt_grad)
        # we return a dummy value 1, which will be scaled by amp's scaler so we get the scale in backward.
        return torch.ones([1], device=input_tensor.device, dtype=input_tensor.dtype)

    @staticmethod
    @custom_bwd
    def backward(ctx, grad_scale):
        gt_grad, = ctx.saved_tensors
        gt_grad = gt_grad * grad_scale
        return gt_grad, None


def seed_everything(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)


class StableDiffusion(nn.Module):
    MODEL_KEYS = {
        '1.5': "runwayml/stable-diffusion-v1-5",
        '2.0': "stabilityai/stable-diffusion-2-base",
        '2.1': "stabilityai/stable-diffusion-2-1-base",
    }

    REQUIRED_SUBFOLDERS = ("vae", "tokenizer", "text_encoder", "unet", "scheduler")

    def __init__(
        self,
        device,
        sd_version='2.1',
        hf_key=None,
        min=0.02,
        max=0.98,
        local_files_only=False,
        cache_dir=None,
        use_auth_token=None,
        allow_fallback=True,
    ):
        super().__init__()

        self.device = device
        self.sd_version = sd_version

        print(f'[INFO] loading stable diffusion...')

        if hf_key is not None:
            print(f'[INFO] using hugging face custom model key: {hf_key}')
            model_keys = [hf_key]
        else:
            if self.sd_version not in self.MODEL_KEYS:
                raise ValueError(
                    f'Stable-diffusion version {self.sd_version} not supported. '
                    f'Choose one of: {list(self.MODEL_KEYS.keys())} or pass --hf_key.'
                )
            primary_model_key = self.MODEL_KEYS[self.sd_version]
            model_keys = [primary_model_key]
            # Some environments cannot access SD2.x (license/auth/network constraints). Fallback keeps runs working.
            if allow_fallback and primary_model_key != self.MODEL_KEYS['1.5']:
                model_keys.append(self.MODEL_KEYS['1.5'])

        if not (0.0 <= min < max <= 1.0):
            raise ValueError(f'Invalid min/max diffusion step range: min={min}, max={max}. Expected 0 <= min < max <= 1.')

        last_error = None
        loaded_model_key = None
        for model_key in model_keys:
            local_name_collision = os.path.isdir(model_key)
            if '/' in model_key and os.path.isdir(model_key.split('/')[0]):
                print(
                    f"[WARN] Found local directory '{model_key.split('/')[0]}' in cwd. "
                    "If model loading fails, this local folder name can shadow a Hugging Face repo ID."
                )

            effective_model_key = self._prepare_local_model_dir(
                model_key=model_key,
                cache_dir=cache_dir,
                local_files_only=local_files_only,
                use_auth_token=use_auth_token,
            )

            pretrained_kwargs = {
                "subfolder": None,  # will be overridden below
                "local_files_only": local_files_only,
                "cache_dir": cache_dir,
                "use_auth_token": use_auth_token,
            }

            try:
                self.vae = AutoencoderKL.from_pretrained(
                    effective_model_key, **{**pretrained_kwargs, "subfolder": "vae"}
                ).to(self.device)
                self.tokenizer = CLIPTokenizer.from_pretrained(
                    effective_model_key, **{**pretrained_kwargs, "subfolder": "tokenizer"}
                )
                self.text_encoder = CLIPTextModel.from_pretrained(
                    effective_model_key, **{**pretrained_kwargs, "subfolder": "text_encoder"}
                ).to(self.device)
                self.unet = UNet2DConditionModel.from_pretrained(
                    effective_model_key, **{**pretrained_kwargs, "subfolder": "unet"}
                ).to(self.device)
                self.scheduler = DDIMScheduler.from_pretrained(
                    effective_model_key, **{**pretrained_kwargs, "subfolder": "scheduler"}
                )
                loaded_model_key = model_key
                break
            except OSError as e:
                last_error = e
                if len(model_keys) > 1:
                    print(f"[WARN] Failed loading '{model_key}', trying fallback model...")
                continue

        if loaded_model_key is None:
            hints = [
                f"Models attempted: {model_keys}",
                f"local_files_only={local_files_only}",
            ]
            if hf_key is not None and os.path.isdir(hf_key):
                hints.append("You passed a local directory via --hf_key; ensure it contains tokenizer/vae/unet/text_encoder/scheduler.")
            else:
                hints.append("If this is a Hub model, verify internet access or use --sd_version 1.5 (public fallback).")
                hints.append("If the model requires auth, run 'huggingface-cli login' and/or pass --hf_token.")
            if last_error is not None and "does not have an ETag" in str(last_error):
                hints.append("Your environment/proxy strips ETag headers. Pre-download once and run with --sd_local_files_only.")
            raise RuntimeError("Failed to load Stable Diffusion components.\n" + "\n".join(hints)) from last_error
        elif loaded_model_key != model_keys[0]:
            print(f"[INFO] Using fallback Stable Diffusion model: {loaded_model_key}")

        if is_xformers_available():
            self.unet.enable_xformers_memory_efficient_attention()

        # self.ts_sampler = TimestepSampler(self.scheduler, device=device)
        # self.scheduler = PNDMScheduler.from_pretrained(model_key, subfolder="scheduler")

        self.num_train_timesteps = self.scheduler.config.num_train_timesteps
        self.min_step = int(self.num_train_timesteps * min)
        self.max_step = int(self.num_train_timesteps * max)
        self.alphas = self.scheduler.alphas_cumprod.to(self.device)  # for convenience

        print(f'[INFO] loaded stable diffusion!')

    def _prepare_local_model_dir(self, model_key, cache_dir, local_files_only, use_auth_token):
        # If a full local model dir is provided, prefer loading from disk directly.
        if os.path.isdir(model_key):
            return model_key

        if local_files_only:
            return model_key

        # Best effort: snapshot the model locally first to avoid fragile per-file ETag checks.
        if snapshot_download is None:
            return model_key

        try:
            # Handle huggingface_hub API differences across versions.
            sig = inspect.signature(snapshot_download)
            kwargs = {
                "repo_id": model_key,
                "cache_dir": cache_dir,
                "local_files_only": False,
            }
            if "token" in sig.parameters:
                kwargs["token"] = use_auth_token
            elif "use_auth_token" in sig.parameters:
                kwargs["use_auth_token"] = use_auth_token

            # Older/newer hub versions differ on this flag.
            if "local_dir_use_symlinks" in sig.parameters:
                kwargs["local_dir_use_symlinks"] = False

            snapshot_path = snapshot_download(**kwargs)
            snapshot_path = Path(snapshot_path)
            if all((snapshot_path / sub).exists() for sub in self.REQUIRED_SUBFOLDERS):
                print(f"[INFO] Using local snapshot for model '{model_key}': {snapshot_path}")
                return str(snapshot_path)
            print(f"[WARN] Snapshot for '{model_key}' is incomplete at {snapshot_path}, falling back to direct loading.")
        except Exception:
            # Fall back to normal loading path; outer try/except will emit actionable errors.
            print(f"[WARN] snapshot_download failed for '{model_key}', falling back to direct loading.")

        return model_key


    def get_text_embeds(self, prompt, negative_prompt=[''], batch=1):
        # prompt, negative_prompt: [str]

        # Tokenize text and get embeddings
        text_input = self.tokenizer(prompt, padding='max_length', max_length=self.tokenizer.model_max_length,
                                    truncation=True, return_tensors='pt')

        with torch.no_grad():
            text_embeddings = self.text_encoder(text_input.input_ids.to(self.device))[0]

        B, S = text_embeddings.shape[:2]
        text_embeddings = text_embeddings.repeat(1, batch, 1).view(B * batch, S, -1)

        # Do the same for unconditional embeddings
        uncond_input = self.tokenizer(negative_prompt, padding='max_length', max_length=self.tokenizer.model_max_length, return_tensors='pt')

        with torch.no_grad():
            uncond_embeddings = self.text_encoder(uncond_input.input_ids.to(self.device))[0]

        B, S = uncond_embeddings.shape[:2]
        uncond_embeddings = uncond_embeddings.repeat(1, batch, 1).view(B * batch, S, -1)

        # Cat for final embeddings
        text_embeddings = torch.cat([uncond_embeddings, text_embeddings])
        return text_embeddings


    def batch_train_step(self, text_embeddings, pred_rgb, guidance_scale=30, as_latent=False, min_step=0.02, max_step=0.98, phi=0.5, return_t=False):
        B = pred_rgb.shape[0]
        min_step = int(self.num_train_timesteps * min_step)
        max_step = int(self.num_train_timesteps * max_step)

        if as_latent:
            # directly downsample input as latent
            latents = F.interpolate(pred_rgb, (64, 64), mode='bilinear', align_corners=False) * 2 - 1
        else:
            if pred_rgb.shape[-1] != 512:
                # interp to 512x512 to be fed into vae.
                pred_rgb_512 = F.interpolate(pred_rgb, (512, 512), mode='bilinear', align_corners=False)
            else:
                pred_rgb_512 = pred_rgb
            # encode image into latents with vae, requires grad!
            latents = self.encode_imgs(pred_rgb_512)

        # timestep ~ U(0.02, 0.98) to avoid very high/low noise level
        t = torch.randint(min_step, max_step + 1, [1], dtype=torch.long, device=self.device).repeat(B)

        # predict the noise residual with unet, NO grad!
        with torch.no_grad():
            # add noise
            noise = torch.randn_like(latents)
            latents_noisy = self.scheduler.add_noise(latents, noise, t)
            # pred noise
            latent_model_input = torch.cat([latents_noisy] * 2)
            tt = torch.cat([t] * 2)
            noise_pred = self.unet(latent_model_input, tt, encoder_hidden_states=text_embeddings).sample

        # perform guidance (high scale from paper!)
        noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
        noise_pred = noise_pred_text + guidance_scale * (noise_pred_text - noise_pred_uncond)

        # w(t), sigma_t^2
        w = (1 - self.alphas[t])
        grad = w.view(-1, 1, 1, 1) * (noise_pred - noise)

        # clip grad for stable training?
        grad = torch.nan_to_num(grad)

        # since we omitted an item in grad, we need to use the custom function to specify the gradient
        loss = SpecifyGradient.apply(latents, grad)

        if return_t:
            return loss, t
        else:
            return loss


    @torch.no_grad()
    def refine(self, text_embeddings, pred_rgb, guidance_scale=100, steps=50, strength=0.8):

        batch_size = pred_rgb.shape[0]
        pred_rgb_512 = F.interpolate(pred_rgb, (512, 512), mode='bilinear', align_corners=False)
        latents = self.encode_imgs(pred_rgb_512)
        # latents = torch.randn((1, 4, 64, 64), device=self.device, dtype=self.dtype)

        self.scheduler.set_timesteps(steps)
        init_step = int(steps * strength)
        latents = self.scheduler.add_noise(latents, torch.randn_like(latents), self.scheduler.timesteps[init_step])

        for i, t in enumerate(self.scheduler.timesteps[init_step:]):
            latent_model_input = torch.cat([latents] * 2)

            noise_pred = self.unet(latent_model_input, t, encoder_hidden_states=text_embeddings).sample

            noise_pred_uncond, noise_pred_cond = noise_pred.chunk(2)
            noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_cond - noise_pred_uncond)

            latents = self.scheduler.step(noise_pred, t, latents).prev_sample

        imgs = self.decode_latents(latents)  # [1, 3, 512, 512]
        return imgs

    def produce_latents(self, text_embeddings, height=512, width=512, num_inference_steps=50, guidance_scale=7.5,
                        latents=None):

        if latents is None:
            latents = torch.randn((text_embeddings.shape[0] // 2, self.unet.in_channels, height // 8, width // 8),
                                  device=self.device)

        self.scheduler.set_timesteps(num_inference_steps)

        with torch.autocast('cuda'):
            for i, t in enumerate(self.scheduler.timesteps):
                # expand the latents if we are doing classifier-free guidance to avoid doing two forward passes.
                latent_model_input = torch.cat([latents] * 2)

                # predict the noise residual
                with torch.no_grad():
                    noise_pred = self.unet(latent_model_input, t, encoder_hidden_states=text_embeddings)['sample']

                # perform guidance
                noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
                noise_pred = noise_pred_text + guidance_scale * (noise_pred_text - noise_pred_uncond)

                # compute the previous noisy sample x_t -> x_t-1
                latents = self.scheduler.step(noise_pred, t, latents)['prev_sample']

        return latents

    def decode_latents(self, latents):

        latents = 1 / 0.18215 * latents

        with torch.no_grad():
            imgs = self.vae.decode(latents).sample

        imgs = (imgs / 2 + 0.5).clamp(0, 1)

        return imgs

    def encode_imgs(self, imgs):
        # imgs: [B, 3, H, W]

        imgs = 2 * imgs - 1

        posterior = self.vae.encode(imgs).latent_dist
        latents = posterior.sample() * 0.18215

        return latents

    def prompt_to_img(self, prompts, negative_prompts='', height=512, width=512, num_inference_steps=50,
                      guidance_scale=7.5, latents=None):

        if isinstance(prompts, str):
            prompts = [prompts]

        if isinstance(negative_prompts, str):
            negative_prompts = [negative_prompts]

        # Prompts -> text embeds
        text_embeds = self.get_text_embeds(prompts, negative_prompts)  # [2, 77, 768]

        # Text embeds -> img latents
        latents = self.produce_latents(text_embeds, height=height, width=width, latents=latents,
                                       num_inference_steps=num_inference_steps,
                                       guidance_scale=guidance_scale)  # [1, 4, 64, 64]

        # Img latents -> imgs
        imgs = self.decode_latents(latents)  # [1, 3, 512, 512]

        # Img to Numpy
        imgs = imgs.detach().cpu().permute(0, 2, 3, 1).numpy()
        imgs = (imgs * 255).round().astype('uint8')

        return imgs


if __name__ == '__main__':
    import argparse
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', default='', type=str)
    parser.add_argument('--negative', default='', type=str)
    parser.add_argument('--sd_version', type=str, default='2.1', choices=['1.5', '2.0', '2.1'],
                        help="stable diffusion version")
    parser.add_argument('--hf_key', type=str, default=None, help="hugging face Stable diffusion model key")
    parser.add_argument('-H', type=int, default=512)
    parser.add_argument('-W', type=int, default=512)
    parser.add_argument('--seed', type=int, default=50)
    parser.add_argument('--steps', type=int, default=50)
    opt = parser.parse_args()

    seed_everything(opt.seed)

    device = torch.device('cuda')

    sd = StableDiffusion(device, opt.sd_version, opt.hf_key)

    imgs = sd.prompt_to_img(opt.prompt, opt.negative, opt.H, opt.W, opt.steps)

    # visualize image
    plt.imshow(imgs[0])
    plt.show()



