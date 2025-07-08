"""RFC 4 implementation for anatomical orientation in OME-NGFF.

This module implements RFC 4 which adds anatomical orientation support
to OME-NGFF axes, based on the LinkML schema.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum


class AnatomicalOrientationValues(str, Enum):
    """
    Anatomical orientation refers to the specific arrangement and directional
    alignment of anatomical structures within an imaging dataset. It is crucial
    for ensuring accurate alignment and comparison of images to anatomical atlases,
    facilitating consistent analysis and interpretation of biological data.
    """

    # Describes the directional orientation from the left side to the right lateral side
    left_to_right = "left-to-right"
    # Describes the directional orientation from the right side to the left lateral side
    right_to_left = "right-to-left"
    # Describes the directional orientation from the front (anterior) to the back (posterior)
    anterior_to_posterior = "anterior-to-posterior"
    # Describes the directional orientation from the back (posterior) to the front (anterior)
    posterior_to_anterior = "posterior-to-anterior"
    # Describes the directional orientation from below (inferior) to above (superior)
    inferior_to_superior = "inferior-to-superior"
    # Describes the directional orientation from above (superior) to below (inferior)
    superior_to_inferior = "superior-to-inferior"
    # Describes the directional orientation from the top/upper (dorsal) to the belly/lower (ventral)
    dorsal_to_ventral = "dorsal-to-ventral"
    # Describes the directional orientation from the belly/lower (ventral) to the top/upper (dorsal)
    ventral_to_dorsal = "ventral-to-dorsal"
    # Describes the directional orientation from the top/upper (dorsal) to the palm of the hand (palmar)
    dorsal_to_palmar = "dorsal-to-palmar"
    # Describes the directional orientation from the palm of the hand (palmar) to the top/upper (dorsal)
    palmar_to_dorsal = "palmar-to-dorsal"
    # Describes the directional orientation from the top/upper (dorsal) to the sole of the foot (plantar)
    dorsal_to_plantar = "dorsal-to-plantar"
    # Describes the directional orientation from the sole of the foot (plantar) to the top/upper (dorsal)
    plantar_to_dorsal = "plantar-to-dorsal"


@dataclass
class AnatomicalOrientation:
    """Anatomical orientation specification for spatial axes."""

    value: AnatomicalOrientationValues
    type: Literal["anatomical"] = "anatomical"


def itk_lps_to_anatomical_orientation(
    axis_name: str,
) -> Optional[AnatomicalOrientation]:
    """
    Convert ITK LPS coordinate system to anatomical orientation.

    ITK uses the LPS (Left-to-right, Posterior-to-anterior, Superior-to-inferior)
    coordinate system by default.

    Parameters
    ----------
    axis_name : str
        The axis name ('x', 'y', or 'z')

    Returns
    -------
    Optional[AnatomicalOrientation]
        The corresponding anatomical orientation, or None for non-spatial axes
    """
    lps_orientations = {
        "x": AnatomicalOrientation(
            type="anatomical", value=AnatomicalOrientationValues.left_to_right
        ),
        "y": AnatomicalOrientation(
            type="anatomical", value=AnatomicalOrientationValues.posterior_to_anterior
        ),
        "z": AnatomicalOrientation(
            type="anatomical", value=AnatomicalOrientationValues.inferior_to_superior
        ),
    }
    return lps_orientations.get(axis_name)


def is_rfc4_enabled(enabled_rfcs: Optional[list[int]]) -> bool:
    """Check if RFC 4 is enabled in the list of enabled RFCs."""
    return enabled_rfcs is not None and 4 in enabled_rfcs


def add_anatomical_orientation_to_axis(
    axis_dict: dict, orientation: AnatomicalOrientation
) -> dict:
    """
    Add anatomical orientation to an axis dictionary.

    Parameters
    ----------
    axis_dict : dict
        The axis dictionary to modify
    orientation : AnatomicalOrientation
        The anatomical orientation to add

    Returns
    -------
    dict
        The modified axis dictionary
    """
    axis_dict["orientation"] = {
        "type": orientation.type,
        "value": orientation.value.value,
    }
    return axis_dict


def remove_anatomical_orientation_from_axis(axis_dict: dict) -> dict:
    """
    Remove anatomical orientation from an axis dictionary.

    Parameters
    ----------
    axis_dict : dict
        The axis dictionary to modify

    Returns
    -------
    dict
        The modified axis dictionary
    """
    if "orientation" in axis_dict:
        axis_dict.pop("orientation")
    return axis_dict
