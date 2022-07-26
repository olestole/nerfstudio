# Copyright 2022 The Plenoptix Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generic utility functions
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from nerfactory.cameras.cameras import (
    Camera,
    get_camera,
    get_intrinsics_from_intrinsics_matrix,
)
from nerfactory.viewer.server.visualizer import Viewer


def get_chunks(
    lst: List[float], num_chunks: Optional[int] = None, size_of_chunk: Optional[int] = None
) -> List[List[float]]:
    """Returns list of n elements, constaining a sublist.

    Args:
        lst: List to be chunked up
        num_chunks: number of chunks to split list into
        size_of_chunk: size of each chunk
    """
    if num_chunks:
        assert not size_of_chunk
        size = len(lst) // num_chunks
    if size_of_chunk:
        assert not num_chunks
        size = size_of_chunk
    chunks = []
    for i in range(0, len(lst), size):
        chunks.append(lst[i : i + size])
    return chunks


def get_intrinsics_matrix_and_camera_to_world_h(
    camera_object: Dict[str, Any], image_height: int
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Returns the camera intrinsics matrix and the camera to world homogeneous matrix.
    Args:
        camera_object: a Camera object.
        image_size: the size of the image (height, width)
    """
    # intrinsics
    fov = camera_object["fov"]
    aspect = camera_object["aspect"]
    image_width = aspect * image_height
    pp_w = image_width / 2.0
    pp_h = image_height / 2.0
    focal_length = pp_h / np.tan(fov * (np.pi / 180.0) / 2.0)
    intrinsics_matrix = torch.tensor([[focal_length, 0, pp_w], [0, focal_length, pp_h], [0, 0, 1]]).float()

    # extrinsics
    camera_to_world_h = torch.tensor(get_chunks(camera_object["matrix"], size_of_chunk=4)).T.float()
    camera_to_world_h = torch.stack(
        [
            camera_to_world_h[0, :],
            camera_to_world_h[2, :],
            camera_to_world_h[1, :],
            camera_to_world_h[3, :],
        ],
        dim=0,
    )

    return intrinsics_matrix, camera_to_world_h


def get_camera_from_vis(vis: Viewer, name: str = "/Cameras/Main Camera", image_height: int = 100) -> Camera:
    """Caculates the specified camera object's parameters (extrinsics/intrinsics); returns associated Camera Object.

    Args:
        vis: viewer object
        name: name of camera to calculate for. Defaults to "/Cameras/Main Camera".
        image_height: height of image. Defaults to 100.
    """
    data = vis[name].get_object()
    if data is None:
        return None
    camera_object = data["object"]["object"]
    intrinsics_matrix, camera_to_world_h = get_intrinsics_matrix_and_camera_to_world_h(
        camera_object, image_height=image_height
    )

    camera_to_world = camera_to_world_h[:3, :]
    intrinsics = get_intrinsics_from_intrinsics_matrix(intrinsics_matrix)
    camera = get_camera(intrinsics, camera_to_world)
    return camera
