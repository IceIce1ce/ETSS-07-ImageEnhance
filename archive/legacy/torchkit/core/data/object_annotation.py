#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Data class for object detection and instance segmentation tasks.
"""

import uuid
from dataclasses import dataclass
from dataclasses import field
from typing import Optional

import numpy as np

from torchkit.core.utils import ID


# MARK: - ObjectAnnotation

def make_default_list() -> list:
	"""Returns an empty list."""
	return []


@dataclass
class ObjectAnnotation:
	"""ObjectAnnotation is a data class used in both ground-truth (i.e,
	dateset annotations) and model predictions (i.e., outputs). We develop a
	common interface and attributes so that the same object can be used in
	several task, such as: detection, tracking, instance seg., etc.

	Attributes:
		id (ID, optional):
			A unique ID. This attribute is useful for database storing and
			tracking task.
		image_id (ID, str, optional):
			The image ID. This attribute is useful for batch processing but
			you want to keep the objects in the correct frame sequence.
		class_id (ID, optional):
			The class ID of the object. This attribute is for query
			additional information about the object.
		bbox (np.ndarray):
			The bounding box of the object in [cx_norm, cy_norm, w_norm, h_norm]
			format (i.e., [center_x_norm, center_y_norm, width_norm_norm,
			height_norm_norm]). We choose this format because it is versatile
			when performing several resize and scale operations.
		rotation (float):
			The bounding box rotation angle. This attribute is useful for
			rotated-bbox detection task.
		segmentation (list, optional):
			The list of vertices (x, y pixel positions) flatten to a 1D array.
			In COCO format, one object can have several list of vertices.
			Hence, it is represented as a 2D arrays.
		keypoints (list):
		
		area (float):
			The area of the bounding box. It is a pixel value.
		confidence (float):
			The confident score of the bounding box or segmentation.
		truncation (float):
			Indicates the degree of object parts appears outside a frame. In
			some datasets, it's value is in [0.0, 1.0] indicates the
			percentage of truncation. In other datasets, it's value is either
			0 (fully visible 0%) or 1 (partially visible 1% ∼ 50%).
		occlusion (float):
			Indicates the fraction of objects being occluded.
			- No occlusion      = 0 (occlusion ratio 0%).
			- Partial occlusion = 1 (occlusion ratio 1% ∼ 50%).
			- Heavy occlusion   = 2 (occlusion ratio 50% ~ 100%)).
		difficult (float):
			An object is marked as difficult when the object is considered
			difficult to recognize. If the object is difficult to recognize
			then we set difficult to 1 else set it to 0.
		
	References:
		- COCO annotations: https://towardsdatascience.com/how-to-work-with-object-detection-datasets-in-coco-format-9bf4fb5848a4
		- DataClass: https://realpython.com/python-data-classes/
	"""

	id          : ID       	   		   = uuid.uuid4().int
	image_id    : Optional[ID] 		   = None
	class_id    : Optional[ID] 		   = None
	bbox        : Optional[np.ndarray] = np.zeros([4, ], np.float32)
	# Creates array [0.0, 0.0, 0.0, 0.0]
	rotation    : float = 0.0
	segmentation: list  = field(default_factory=make_default_list)
	keypoints   : list 	= field(default_factory=make_default_list)
	area        : float = 0.0
	confidence  : float = 1.0
	truncation  : float = 0
	occlusion   : float = 0
	difficult   : float = 0
	is_crowd    : int 	= 0
	
	# MARK: Properties
	
	@property
	def bbox_label(self) -> np.ndarray:
		"""Return bounding box label for detection task.

		Returns:
			bbox_label (np.ndarray):
				A numpy array: [<image_id>, <class_id>, <cx_norm>, <cy_norm>,
				<w_norm>, <h_norm>, <confidence>, <area>, <truncation>,
				<occlusion>]
		"""
		return np.array(
			[
				self.image_id, self.class_id, self.bbox[0], self.bbox[1],
				self.bbox[2], self.bbox[3], self.confidence, self.area,
				self.truncation, self.occlusion
			],
			dtype=np.float32
		)
	
	@classmethod
	def bbox_label_len(cls) -> int:
		"""Return the len of a single bbox_label (i.e, the number of features).
		"""
		return 10
	
	@property
	def segmentation_vertices(self) -> list:
		"""Reformat the `segmentation` as a list of vertices.
		For example: [ [point1_x, point1_y], [point2_x, point2_y], ...].
		"""
		segments = []
		for s in self.segmentation:
			v  = []
			it = iter(s)
			for p in it:  # Loop through 2 items at a time
				v.append([p, next(it)])
			segments.append(v)
		return segments
	
	@segmentation_vertices.setter
	def segmentation_vertices(self, segments: list):
		"""Assign `segmentation` attribute with a list of vertices.
		For example: [ [point1_x, point1_y], [point2_x, point2_y], ...].
		"""
		segmentations = []
		for seg in segments:
			s = []
			for v in seg:
				s.append(v[0])
				s.append(v[1])
			segmentations.append(s)
		self.segmentation = segmentations
	
	@property
	def polygon(self) -> list:
		"""Alias of `segmentation`."""
		return self.segmentation
	
	@polygon.setter
	def polygon(self, polygon: list):
		self.segmentation = polygon
	
	@property
	def polygon_vertices(self) -> list:
		"""Alias of `segmentation_vertices`."""
		return self.segmentation_vertices
	
	@polygon_vertices.setter
	def polygon_vertices(self, polygon: list):
		self.segmentation_vertices = polygon
	
	@property
	def num_keypoints(self) -> int:
		"""Return the number of keypoints."""
		if self.keypoints is not None:
			return int(len(self.keypoints) / 2)
		return 0
