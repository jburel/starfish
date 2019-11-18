import numpy as np
import pytest

from starfish.core.types import Axes, Coordinates
from ..binary_mask import BinaryMaskCollection


def test_2d():
    """Simple case of BinaryMaskCollection.from_label_array_and_ticks with 2D data.  Pixel ticks are
    inferred."""
    label_image_array = np.zeros((5, 6), dtype=np.int32)
    label_image_array[0] = 1
    label_image_array[3:5, 3:6] = 2
    label_image_array[-1, -1] = 0

    physical_ticks = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                      Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]}

    binary_mask_collection = BinaryMaskCollection.from_label_array_and_ticks(
        label_image_array,
        None,
        physical_ticks,
        None
    )
    assert len(binary_mask_collection) == 2

    region_0, region_1 = binary_mask_collection.masks()
    assert region_0.name == '0'
    assert region_1.name == '1'

    assert np.array_equal(region_0, np.ones((1, 6), dtype=np.bool))
    temp = np.ones((2, 3), dtype=np.bool)
    temp[-1, -1] = False
    assert np.array_equal(region_1, temp)

    assert np.array_equal(region_0[Axes.Y.value], [0])
    assert np.array_equal(region_0[Axes.X.value], [0, 1, 2, 3, 4, 5])

    assert np.array_equal(region_1[Axes.Y.value], [3, 4])
    assert np.array_equal(region_1[Axes.X.value], [3, 4, 5])

    assert np.array_equal(region_0[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][0:1])
    assert np.array_equal(region_0[Coordinates.X.value],
                          physical_ticks[Coordinates.X][0:6])

    assert np.array_equal(region_1[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][3:5])
    assert np.array_equal(region_1[Coordinates.X.value],
                          physical_ticks[Coordinates.X][3:6])


def test_3d():
    """Simple case of BinaryMaskCollection.from_label_array_and_ticks with 3D data.  Pixel ticks are
    inferred."""
    label_image_array = np.zeros((2, 5, 6), dtype=np.int32)
    label_image_array[0, 0] = 1
    label_image_array[:, 3:5, 3:6] = 2
    label_image_array[-1, -1, -1] = 0

    physical_ticks = {
        Coordinates.Z: [0.0, 1.0],
        Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
        Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]
    }

    binary_mask_collection = BinaryMaskCollection.from_label_array_and_ticks(
        label_image_array,
        None,
        physical_ticks,
        None
    )
    assert len(binary_mask_collection) == 2

    region_0, region_1 = binary_mask_collection.masks()
    assert region_0.name == '0'
    assert region_1.name == '1'

    assert np.array_equal(region_0, np.ones((1, 1, 6), dtype=np.bool))
    temp = np.ones((2, 2, 3), dtype=np.bool)
    temp[-1, -1, -1] = False
    assert np.array_equal(region_1, temp)

    assert np.array_equal(region_0[Axes.ZPLANE.value], [0])
    assert np.array_equal(region_0[Axes.Y.value], [0])
    assert np.array_equal(region_0[Axes.X.value], [0, 1, 2, 3, 4, 5])

    assert np.array_equal(region_1[Axes.ZPLANE.value], [0, 1])
    assert np.array_equal(region_1[Axes.Y.value], [3, 4])
    assert np.array_equal(region_1[Axes.X.value], [3, 4, 5])

    assert np.array_equal(region_0[Coordinates.Z.value],
                          physical_ticks[Coordinates.Z][0:1])
    assert np.array_equal(region_0[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][0:1])
    assert np.array_equal(region_0[Coordinates.X.value],
                          physical_ticks[Coordinates.X][0:6])

    assert np.array_equal(region_1[Coordinates.Z.value],
                          physical_ticks[Coordinates.Z][0:2])
    assert np.array_equal(region_1[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][3:5])
    assert np.array_equal(region_1[Coordinates.X.value],
                          physical_ticks[Coordinates.X][3:6])


def test_from_label_array_provided_pixel_ticks():
    """BinaryMaskCollection.from_label_array_and_ticks with 2D data and some pixel ticks
    provided."""
    label_image_array = np.zeros((5, 6), dtype=np.int32)
    label_image_array[0] = 1
    label_image_array[3:5, 3:6] = 2
    label_image_array[-1, -1] = 0

    pixel_ticks = {
        Axes.X: [2, 3, 4, 5, 6, 7],
    }
    physical_ticks = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                      Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]}

    binary_mask_collection = BinaryMaskCollection.from_label_array_and_ticks(
        label_image_array,
        pixel_ticks,
        physical_ticks,
        None
    )
    assert len(binary_mask_collection) == 2

    region_0, region_1 = binary_mask_collection.masks()
    assert region_0.name == '0'
    assert region_1.name == '1'

    assert np.array_equal(region_0, np.ones((1, 6), dtype=np.bool))
    temp = np.ones((2, 3), dtype=np.bool)
    temp[-1, -1] = False
    assert np.array_equal(region_1, temp)

    assert np.array_equal(region_0[Axes.Y.value], [0])
    assert np.array_equal(region_0[Axes.X.value], [2, 3, 4, 5, 6, 7])

    assert np.array_equal(region_1[Axes.Y.value], [3, 4])
    assert np.array_equal(region_1[Axes.X.value], [5, 6, 7])

    assert np.array_equal(region_0[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][0:1])
    assert np.array_equal(region_0[Coordinates.X.value],
                          physical_ticks[Coordinates.X][0:6])

    assert np.array_equal(region_1[Coordinates.Y.value],
                          physical_ticks[Coordinates.Y][3:5])
    assert np.array_equal(region_1[Coordinates.X.value],
                          physical_ticks[Coordinates.X][3:6])


def test_incorrectly_sized_pixel_ticks():
    """BinaryMaskCollection.from_label_array_and_ticks with 2D data and some pixel ticks provided,
    albeit of the wrong cardinality."""
    label_image_array = np.zeros((5, 6), dtype=np.int32)
    label_image_array[0] = 1
    label_image_array[3:5, 3:6] = 2
    label_image_array[-1, -1] = 0

    pixel_ticks = {
        Axes.X: [2, 3, 4, 5, 6, 7, 8],
    }
    physical_ticks = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                      Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]}

    with pytest.raises(ValueError):
        BinaryMaskCollection.from_label_array_and_ticks(
            label_image_array,
            pixel_ticks,
            physical_ticks,
            None
        )


def test_missing_physical_ticks():
    """BinaryMaskCollection.from_label_array_and_ticks with some physical ticks missing."""
    label_image_array_2d = np.zeros((5, 6), dtype=np.int32)
    label_image_array_2d[0] = 1
    label_image_array_2d[3:5, 3:6] = 2
    label_image_array_2d[-1, -1] = 0

    physical_ticks_2d_all = {
        Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
        Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]
    }

    for physical_coordinate_type in physical_ticks_2d_all.keys():
        physical_ticks_2d = physical_ticks_2d_all.copy()
        del physical_ticks_2d[physical_coordinate_type]
        with pytest.raises(ValueError):
            BinaryMaskCollection.from_label_array_and_ticks(
                label_image_array_2d,
                None,
                physical_ticks_2d,
                None
            )

    label_image_array_3d = np.zeros((2, 5, 6), dtype=np.int32)
    label_image_array_3d[0, 0] = 1
    label_image_array_3d[:, 3:5, 3:6] = 2
    label_image_array_3d[-1, -1, -1] = 0

    physical_ticks_3d_all = {
        Coordinates.Z: [0.0, 1.0],
        Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
        Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]
    }

    for physical_coordinate_type in physical_ticks_3d_all.keys():
        physical_ticks_3d = physical_ticks_3d_all.copy()
        del physical_ticks_3d[physical_coordinate_type]
        with pytest.raises(ValueError):
            BinaryMaskCollection.from_label_array_and_ticks(
                label_image_array_3d,
                None,
                physical_ticks_3d,
                None
            )


def test_incorrectly_sized_physical_ticks():
    """BinaryMaskCollection.from_label_array_and_ticks with some physical ticks incorrectly
    sized."""
    label_image_array_2d = np.zeros((5, 6), dtype=np.int32)
    label_image_array_2d[0] = 1
    label_image_array_2d[3:5, 3:6] = 2
    label_image_array_2d[-1, -1] = 0

    physical_ticks_2d = {Coordinates.Y: [1.2, 2.4, 3.6, 4.8, 6.0],
                         Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12]}

    with pytest.raises(ValueError):
        BinaryMaskCollection.from_label_array_and_ticks(
            label_image_array_2d,
            None,
            physical_ticks_2d,
            None
        )

    label_image_array_3d = np.zeros((2, 5, 6), dtype=np.int32)
    label_image_array_3d[0, 0] = 1
    label_image_array_3d[:, 3:5, 3:6] = 2
    label_image_array_3d[-1, -1, -1] = 0

    physical_ticks_3d = {
        Coordinates.Z: [0.0, 1.0],
        Coordinates.Y: [1.2, 2.4, 3.6, 4.8],
        Coordinates.X: [7.2, 8.4, 9.6, 10.8, 12, 13.2]
    }

    with pytest.raises(ValueError):
        BinaryMaskCollection.from_label_array_and_ticks(
            label_image_array_3d,
            None,
            physical_ticks_3d,
            None
        )
