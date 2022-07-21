import shutil
from pathlib import Path
from typing import List, Tuple

import mrcfile
import numpy as np


def prepare_output_directory(
        directory: Path,
        tilt_series: np.ndarray,
        tilt_angles: List[float],
        basename: str,
        pixel_size: float,
) -> Tuple[Path, Path]:
    directory.mkdir(exist_ok=True, parents=True)

    tilt_series_file = directory / f'{basename}.mrc'
    mrcfile.write(
        tilt_series_file,
        tilt_series.astype(np.float32),
        voxel_size=(pixel_size, pixel_size, 1)
    )

    rawtlt_file = directory / f'{basename}.rawtlt'
    np.savetxt(rawtlt_file, tilt_angles, fmt='%.2f', delimiter='')
    return tilt_series_file, rawtlt_file

def get_aretomo_command(
        tilt_series_file: Path,
        tilt_angle_file: Path,
        reconstruction_filename: Path,
        expected_sample_thickness_px: int,
        binning_factor: float,
        correct_tilt_angle_offset: bool = True,
        nominal_tilt_axis_angle: Optional[float] = None,
        aretomo_executable: Optional[Path] = None,
        do_local_alignments: bool = True,
        n_patches_xy: Optional[Tuple[int, int]] = None,
        gpu_ids: Optional[Sequence[int]] = None
) -> List[str]:
    executable = 'AreTomo' if aretomo_executable is None else str(aretomo_executable)
    command = [
        f'{executable}',
        '-InMrc', f'{tilt_series_file}',
        '-OutMrc', f'{reconstruction_filename}',
        '-OutBin', f'{binning_factor:.3f}',
        '-AngFile', f'{tilt_angle_file}',
        '-AlignZ', f'{expected_sample_thickness_px}',
        '-VolZ', f'{int(1.5 * expected_sample_thickness_px)}',
        '-DarkTol', '0.01',  # this ensures bad images are not automatically removed
    ]
    if nominal_tilt_axis_angle is not None:
        command += ['-TiltAxis', f'{nominal_tilt_axis_angle}']
    if do_local_alignments is True:
        command += ['-Patch', f'{n_patches_xy[0]}', f'{n_patches_xy[1]}']
    if correct_tilt_angle_offset is True:
        command += ['-TiltCor', '1']
    if gpu_ids is not None:
        command += ['-Gpu'] + [f'{gpu_id}' for gpu_id in gpu_ids]
    return command

def check_aretomo_is_installed():
    """Check for an installation of AreTomo on the PATH."""
    return shutil.which('AreTomo') is not None
