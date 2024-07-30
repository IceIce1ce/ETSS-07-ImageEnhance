#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module implements the base model class for classification models."""

from __future__ import annotations

__all__ = [
    "ImageClassificationModel",
]

from abc import ABC

from mon import core, nn
from mon.globals import Task, ZOO_DIR

console = core.console


# region Model

class ImageClassificationModel(nn.Model, ABC):
    """The base class for all image classification models.
    
    See Also: :class:`nn.Model`.
    """
    
    tasks  : list[Task] = [Task.CLASSIFY]
    zoo_dir: core.Path  = ZOO_DIR / "vision" / "classify"
    
# endregion
