#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------
# Copyright (c) 2021 megvii-model. All Rights Reserved.
# ------------------------------------------------------------------------
# Modified from BasicSR (https://github.com/xinntao/BasicSR)
# Copyright 2018-2020 BasicSR Authors
# ------------------------------------------------------------------------

from __future__ import annotations

from collections import OrderedDict
from os import path as osp

import yaml

from mon import RUN_DIR


def ordered_yaml():
    """Support OrderedDict for yaml.

    Returns:
        yaml Loader and Dumper.
    """
    try:
        from yaml import CDumper as Dumper
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Dumper, Loader

    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())

    def dict_constructor(loader, node):
        return OrderedDict(loader.construct_pairs(node))

    Dumper.add_representer(OrderedDict, dict_representer)
    Loader.add_constructor(_mapping_tag, dict_constructor)
    return Loader, Dumper


def parse(opt_path: str, is_train: bool = True) -> dict:
    """Parse option file.

    Args:
        opt_path: Option file path.
        is_train: Indicate whether in training or not. Default: ``True``.

    Returns:
        Options.
    """
    with open(opt_path, mode="r") as f:
        loader, _ = ordered_yaml()
        opt       = yaml.load(f, Loader=loader)

    opt["is_train"] = is_train

    # Datasets
    if "datasets" in opt:
        for phase, dataset in opt["datasets"].items():
            # for several datasets, e.g., test_1, test_2
            phase = phase.split("_")[0]
            dataset["phase"] = phase
            if "scale" in opt:
                dataset["scale"] = opt["scale"]
            if dataset.get("dataroot_gt") is not None:
                dataset["dataroot_gt"] = osp.expanduser(dataset["dataroot_gt"])
            if dataset.get("dataroot_lq") is not None:
                dataset["dataroot_lq"] = osp.expanduser(dataset["dataroot_lq"])

    # paths
    for key, val in opt["path"].items():
        if (val is not None) and ("resume_state" in key or "pretrain_network" in key):
            opt["path"][key] = osp.expanduser(val)

    # opt["path"]["root"] = osp.abspath(osp.join(__file__, osp.pardir, osp.pardir, osp.pardir))
    if is_train:
        opt["path"]["root"] = str(RUN_DIR / "train/vision/enhance/universal/hinet")
        # experiments_root = osp.join(opt["path"]["root"], "experiments", opt["name"])
        experiments_root = str(RUN_DIR / "train/vision/enhance/universal/hinet" / opt["name"])
        opt["path"]["experiments_root"] = experiments_root
        opt["path"]["models"]           = osp.join(experiments_root, "models")
        opt["path"]["training_states"]  = osp.join(experiments_root, "training_states")
        opt["path"]["log"]              = experiments_root
        opt["path"]["visualization"]    = osp.join(experiments_root, "visualization")

        # Change some options for debug mode
        if "debug" in opt["name"]:
            if "val" in opt:
                opt["val"]["val_freq"] = 8
            opt["logger"]["print_freq"] = 1
            opt["logger"]["save_checkpoint_freq"] = 8
    else:  # test
        opt["path"]["root"] = str(RUN_DIR / "predict/vision/enhance/universal/hinet")
        # results_root = osp.join(opt["path"]["root"], "results", opt["name"])
        results_root = str(RUN_DIR / "predict/vision/enhance/universal/hinet" / opt["name"])
        opt["path"]["results_root"]  = results_root
        opt["path"]["log"]           = results_root
        opt["path"]["visualization"] = osp.join(results_root, "visualization")

    return opt


def dict2str(opt, indent_level=1):
    """dict to string for printing options.

    Args:
        opt (dict): Option dict.
        indent_level (int): Indent level. Default: 1.

    Return:
        (str): Option string for printing.
    """
    msg = "\n"
    for k, v in opt.items():
        if isinstance(v, dict):
            msg += " " * (indent_level * 2) + k + ":["
            msg += dict2str(v, indent_level + 1)
            msg += " " * (indent_level * 2) + "]\n"
        else:
            msg += " " * (indent_level * 2) + k + ": " + str(v) + "\n"
    return msg
