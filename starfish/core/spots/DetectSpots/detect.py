from functools import partial
from itertools import product
from typing import Callable, Dict, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr

from starfish.core.imagestack.imagestack import ImageStack
from starfish.core.intensity_table.intensity_table import IntensityTable
from starfish.core.intensity_table.intensity_table_coordinates import \
    transfer_physical_coords_to_intensity_table
from starfish.core.types import Axes, Features, Number, SpotAttributes


def measure_spot_intensity(
        image: Union[np.ndarray, xr.DataArray],
        spots: SpotAttributes,
        measurement_function: Callable[[Union[np.ndarray, xr.DataArray]], Number],
        radius_is_gyration: bool=False,
) -> pd.Series:
    """measure the intensity of each spot in spots in the corresponding image

    Parameters
    ----------
    image : Union[np.ndarray, xr.DataArray],
        3-d volume in which to measure intensities
    spots : pd.DataFrame
        SpotAttributes table containing coordinates and radii of spots
    measurement_function : Callable[[Union[np.ndarray, xr.DataArray]], Number])
        Function to apply over the spot volumes to identify the intensity (e.g. max, mean, ...)
    radius_is_gyration : bool
        if True, indicates that the radius corresponds to radius of gyration, which is a function of
        spot intensity, but typically is a smaller unit than the sigma generated by blob_log.
        In this case, the spot's bounding box is rounded up instead of down when measuring
        intensity. (default False)

    Returns
    -------
    pd.Series :
        Intensities for each spot in SpotAttributes

    """

    def fn(row: pd.Series) -> Number:
        data = image[
            row['z_min']:row['z_max'],
            row['y_min']:row['y_max'],
            row['x_min']:row['x_max']
        ]
        return measurement_function(data)

    if radius_is_gyration:
        radius = np.ceil(spots.data[Features.SPOT_RADIUS]).astype(int) + 1  # round up
    else:
        radius = spots.data[Features.SPOT_RADIUS].astype(int)  # truncate down to nearest integer
    for v, max_size in zip(['z', 'y', 'x'], image.shape):
        # numpy does exclusive max indexing, so need to subtract 1 from min to get centered box
        spots.data[f'{v}_min'] = np.clip(spots.data[v] - (radius - 1), 0, None)
        spots.data[f'{v}_max'] = np.clip(spots.data[v] + radius, None, max_size)
    return spots.data[['z_min', 'z_max', 'y_min', 'y_max', 'x_min', 'x_max']].astype(int).apply(
        fn,
        axis=1
    )


def measure_spot_intensities(
        data_image: ImageStack,
        spot_attributes: SpotAttributes,
        measurement_function: Callable[[Union[np.ndarray, xr.DataArray]], Number],
        radius_is_gyration: bool=False,
) -> IntensityTable:
    """given spots found from a reference image, find those spots across a data_image

    Parameters
    ----------
    data_image : ImageStack
        ImageStack containing multiple volumes for which spots' intensities must be calculated
    spot_attributes : pd.Dataframe
        Locations and radii of spots
    measurement_function : Callable[[Union[np.ndarray, xr.DataArray]], Number])
        Function to apply over the spot volumes to identify the intensity (e.g. max, mean, ...)
    radius_is_gyration : bool
        if True, indicates that the radius corresponds to radius of gyration, which is a function of
        spot intensity, but typically is a smaller unit than the sigma generated by blob_log.
        In this case, the spot's bounding box is rounded up instead of down when measuring
        intensity. (default False)

    Returns
    -------
    IntensityTable :
        3d tensor of (spot, channel, round) information for each coded spot

    """

    # determine the shape of the intensity table
    ch_labels = data_image.axis_labels(Axes.CH)
    round_labels = data_image.axis_labels(Axes.ROUND)

    # construct the empty intensity table
    intensity_table = IntensityTable.zeros(
        spot_attributes=spot_attributes,
        round_labels=round_labels,
        ch_labels=ch_labels,
    )

    # if no spots were detected, return the empty IntensityTable
    if intensity_table.sizes[Features.AXIS] == 0:
        return intensity_table

    # fill the intensity table
    indices = product(ch_labels, round_labels)
    for c, r in indices:
        image, _ = data_image.get_slice({Axes.CH: c, Axes.ROUND: r})
        blob_intensities: pd.Series = measure_spot_intensity(
            image,
            spot_attributes,
            measurement_function,
            radius_is_gyration=radius_is_gyration
        )
        intensity_table.loc[dict(c=c, r=r)] = blob_intensities

    return intensity_table


def concatenate_spot_attributes_to_intensities(
        spot_attributes: Sequence[Tuple[SpotAttributes, Dict[Axes, int]]]
) -> IntensityTable:
    """
    Merge multiple spot attributes frames into a single IntensityTable without merging across
    channels and imaging rounds

    Parameters
    ----------
    spot_attributes : Sequence[Tuple[SpotAttributes, Dict[Axes, int]]]
        A sequence of SpotAttribute objects and the indices (channel, round) that each object is
        associated with.

    Returns
    -------
    IntensityTable :
        concatenated input SpotAttributes, converted to an IntensityTable object

    """
    ch_values: Sequence[int] = sorted(set(inds[Axes.CH] for _, inds in spot_attributes))
    round_values: Sequence[int] = sorted(set(inds[Axes.ROUND] for _, inds in spot_attributes))

    all_spots = pd.concat([sa.data for sa, inds in spot_attributes], sort=True)
    # this drop call ensures only x, y, z, radius, and quality, are passed to the IntensityTable
    features_coordinates = all_spots.drop(['spot_id', 'intensity'], axis=1)

    intensity_table = IntensityTable.zeros(
        SpotAttributes(features_coordinates), round_values, ch_values,
    )

    i = 0
    for attrs, inds in spot_attributes:
        for _, row in attrs.data.iterrows():
            selector = dict(features=i, c=inds[Axes.CH], r=inds[Axes.ROUND])
            intensity_table.loc[selector] = row['intensity']
            i += 1

    return intensity_table


def detect_spots(data_stack: ImageStack,
                 spot_finding_method: Callable[..., SpotAttributes],
                 spot_finding_kwargs: Dict = None,
                 reference_image: Optional[ImageStack] = None,
                 reference_image_max_projection_axes: Optional[Tuple[Axes, ...]] = None,
                 measurement_function: Callable[[Union[np.ndarray, xr.DataArray]], Number] = np.max,
                 radius_is_gyration: bool = False,
                 n_processes: Optional[int] = None) -> IntensityTable:
    """Apply a spot_finding_method to a ImageStack

    Parameters
    ----------
    data_stack : ImageStack
        The ImageStack containing spots
    spot_finding_method : Callable[..., IntensityTable]
        The method to identify spots
    spot_finding_kwargs : Dict
        additional keyword arguments to pass to spot_finding_method
    reference_image : xr.DataArray
        (Optional) a reference image. If provided, spots will be found in this image, and then
        the locations that correspond to these spots will be measured across each channel and round,
        filling in the values in the IntensityTable
    reference_image_max_projection_axes : Tuple[Axes]
        Generate the reference image by max-projecting reference_image across these axes.
    measurement_function : Callable[[Union[np.ndarray, xr.DataArray]], Number]
        the function to apply over the spot area to extract the intensity value (default 'np.max')
    radius_is_gyration : bool
        if True, indicates that the radius corresponds to radius of gyration, which is a function of
        spot intensity, but typically is a smaller unit than the sigma generated by blob_log.
        In this case, the spot's bounding box is rounded up instead of down when measuring
        intensity. (default False)
    is_volume: bool
        If True, pass 3d volumes (x, y, z) to func, else pass 2d tiles (x, y) to func. (default
        True)
    n_processes : Optional[int]
        The number of processes to use in stack.transform if reference image is None.
        If None, uses the output of os.cpu_count() (default = None).

    Notes
    -----
    - This class will always detect spots in 3d. If 2d spot detection is desired, the data should
      be projected down to "fake 3d" prior to submission to this function
    - If neither reference_image nor reference_from_max_projection are passed, spots will be
      detected _independently_ in each channel. This assumes a non-multiplex imaging experiment,
      as only one (ch, round) will be measured for each spot.

    Returns
    -------
    IntensityTable :
        IntensityTable containing the intensity of each spot, its radius, and location in pixel
        coordinates

    """

    if spot_finding_kwargs is None:
        spot_finding_kwargs = {}

    if reference_image is not None:
        if reference_image_max_projection_axes is not None:
            reference_image = reference_image.max_proj(*reference_image_max_projection_axes)
            data_image = reference_image._squeezed_numpy(*reference_image_max_projection_axes)
        else:
            data_image = reference_image.xarray
        reference_spot_locations = spot_finding_method(data_image, **spot_finding_kwargs)
        intensity_table = measure_spot_intensities(
            data_image=data_stack,
            spot_attributes=reference_spot_locations,
            measurement_function=measurement_function,
            radius_is_gyration=radius_is_gyration,
        )
    else:  # don't use a reference image, measure each
        spot_finding_method = partial(spot_finding_method, **spot_finding_kwargs)
        spot_attributes_list = data_stack.transform(
            func=spot_finding_method,
            group_by={Axes.ROUND, Axes.CH},
            n_processes=n_processes
        )
        intensity_table = concatenate_spot_attributes_to_intensities(spot_attributes_list)

    transfer_physical_coords_to_intensity_table(image_stack=data_stack,
                                                intensity_table=intensity_table)

    return intensity_table
