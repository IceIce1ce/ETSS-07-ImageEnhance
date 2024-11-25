#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""XML File Handler.

This module implements the XML file handler by extending the :obj:`xmltodict`
module.
"""

from __future__ import annotations

from typing import Any, TextIO

from xmltodict import *

from mon.core import pathlib
from mon.core.file import base
from mon.globals import FILE_HANDLERS


# region XML File Handler

@FILE_HANDLERS.register(name=".xml")
class XMLHandler(base.FileHandler):
    """XML file handler."""
    
    def read_from_fileobj(
        self,
        path: pathlib.Path | str | TextIO,
        **kwargs
    ) -> Any:
        doc = parse(path.read())
        return doc
    
    def write_to_fileobj(
        self,
        obj : Any,
        path: pathlib.Path | str | TextIO,
        **kwargs
    ):
        if not isinstance(obj, dict):
            raise TypeError(f"`obj` must be a `dict`, but got {type(obj)}.")
        path = pathlib.Path(path)
        with open(path, "w") as f:
            f.write(unparse(input_dict=obj, pretty=True))
    
    def write_to_string(self, obj: Any, **kwargs) -> str:
        assert isinstance(obj, dict)
        return unparse(input_dict=obj, pretty=True)

# endregion
