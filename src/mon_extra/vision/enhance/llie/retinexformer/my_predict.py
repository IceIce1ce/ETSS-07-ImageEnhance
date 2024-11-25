#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import copy

import torch
import torch.nn.functional as F
from skimage.util import img_as_ubyte

import mon
import utils
from basicsr.models import create_model
from basicsr.utils.options import parse

console      = mon.console
current_file = mon.Path(__file__).absolute()
current_dir  = current_file.parents[0]


# region Predict

def predict(args: argparse.Namespace):
    # General config
    opt_path     = str(current_dir / "model_config" / args.opt_path)
    data         = args.data
    save_dir     = mon.Path(args.save_dir)
    weights      = args.weights
    device       = mon.set_device(args.device)
    imgsz        = args.imgsz
    imgsz        = imgsz[0] if isinstance(imgsz, list | tuple) else imgsz
    resize       = args.resize
    benchmark    = args.benchmark
    save_image   = args.save_image
    save_debug   = args.save_debug
    use_fullpath = args.use_fullpath
    
    # Override options with args
    # gpu_list = ",".join(str(x) for x in args.gpus)
    # os.environ["CUDA_VISIBLE_DEVICES"] = gpu_list
    # print("export CUDA_VISIBLE_DEVICES=" + gpu_list)
    opt           = parse(opt_path, is_train=False)
    opt["dist"]   = False
    opt["device"] = device
    
    # Model
    model      = create_model(opt).net_g
    checkpoint = torch.load(weights)
    try:
        model.load_state_dict(checkpoint["params"])
    except:
        new_checkpoint = {}
        for k in checkpoint["params"]:
            new_checkpoint["module." + k] = checkpoint["params"][k]
        model.load_state_dict(new_checkpoint)
    
    # print("===>Testing using weights: ", weights)
    model.to(device)
    # model = nn.DataParallel(model)
    model.eval()
    
    # Benchmark
    # if benchmark:
    #     flops, params, avg_time = copy.deepcopy(model).measure_efficiency_score(image_size=imgsz)
    #     console.log(f"FLOPs  = {flops:.4f}")
    #     console.log(f"Params = {params:.4f}")
    #     console.log(f"Time   = {avg_time:.17f}")
    
    # Data I/O
    console.log(f"[bold red]{data}")
    data_name, data_loader, data_writer = mon.parse_io_worker(
        src         = data,
        dst         = save_dir,
        to_tensor   = True,
        denormalize = True,
        verbose     = False,
    )
    
    # Predicting
    timer  = mon.Timer()
    factor = 4
    with torch.no_grad():
        with mon.get_progress_bar() as pbar:
            for i, datapoint in pbar.track(
                sequence    = enumerate(data_loader),
                total       = len(data_loader),
                description = f"[bright_yellow] Predicting"
            ):
                # Input
                image      = datapoint.get("image")
                meta       = datapoint.get("meta")
                image_path = mon.Path(meta["path"])
                
                if torch.cuda.is_available():
                    torch.cuda.ipc_collect()
                    torch.cuda.empty_cache()
                if resize:
                    h0, w0 = mon.get_image_size(image)
                    image  = mon.resize(image, imgsz)
                    console.log("Resizing images to: ", image.shape[2], image.shape[3])
                    # images = proc.resize(input=images, size=[1000, 666])
                # Padding in case images are not multiples of 4
                h, w  = mon.get_image_size(image)
                H, W  = ((h + factor) // factor) * factor, ((w + factor) // factor) * factor
                padh  = H - h if h % factor != 0 else 0
                padw  = W - w if w % factor != 0 else 0
                input = F.pad(image, (0, padw, 0, padh), 'reflect')
                input = input.to(device)
                
                # Infer
                timer.tick()
                restored = model(input)
                timer.tock()
                
                # Post-processing
                # Unpad images to original dimensions
                restored = restored[:, :, :h, :w]
                if resize:
                    restored = mon.resize(restored, (h0, w0))
                restored = torch.clamp(restored, 0, 1).cpu().detach().permute(0, 2, 3, 1).squeeze(0).numpy()
                
                # Save
                if save_image:
                    if use_fullpath:
                        rel_path    = image_path.relative_path(data_name)
                        output_path = save_dir / rel_path.parent / image_path.name
                    else:
                        output_path = save_dir / data_name / image_path.name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    utils.save_img(str(output_path), img_as_ubyte(restored))
        
        avg_time = float(timer.avg_time)
        console.log(f"Average time: {avg_time}")
        
# endregion


# region Main

def main() -> str:
    args = mon.parse_predict_args(model_root=current_dir)
    predict(args)


if __name__ == "__main__":
    main()

# endregion
