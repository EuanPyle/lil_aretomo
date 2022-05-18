import os
import shutil
import subprocess
from pathlib import Path
from typing import List

import numpy as np

def prepare_output_directory(
        tilt_series_file: Path, 
        tilt_angles: List[float], 
        output_directory: Path
):
    ts_dir_name = tilt_series_file.stem
    output_directory.mkdir(exist_ok=True, parents=True)

    # Link tilt-series file into output directory
    tilt_series_filename = tilt_series_file.with_suffix('.mrc').name
    linked_tilt_series_file = output_directory / tilt_series_filename
    force_symlink(tilt_series_file.absolute(), linked_tilt_series_file)

    rawtlt_file = output_directory / f'{ts_dir_name}.rawtlt'
    np.savetxt(rawtlt_file, tilt_angles, fmt='%.2f', delimiter='')


def align_tilt_series_aretomo(
        tilt_series_file: Path,
        imod_directory: Path,
        binning: float,
        aretomo_executable: Path,
        nominal_rotation_angle: bool or float,
        local_align: bool,
        n_patches_xy: tuple[int, int],
        correct_tilt_angle_offset: bool,
        thickness_for_alignment: float
):
    # Rename file .mrc if .st
    if tilt_series_file.suffix == '.st':
        tilt_series_file = tilt_series_file.with_suffix('.mrc')

    output_file_name = Path(
        f'{imod_directory}/{tilt_series_file.stem}_aln{tilt_series_file.suffix}')

    # Run AreTomo
    aretomo_command = [
        f'{str(aretomo_executable)}',
        '-InMrc', f'{tilt_series_file}',
        '-OutMrc', f'{output_file_name}',
        '-OutBin', f'{binning}',
        '-AngFile', f'{imod_directory}/{tilt_series_file.stem}.rawtlt',
        '-AlignZ', f'{thickness_for_alignment}',
        '-VolZ', '0',
        '-OutXF', '1'
    ]

    if not nominal_rotation_angle == None:
        aretomo_command.append('-TiltAxis')
        aretomo_command.append(f'{nominal_rotation_angle}')

    if local_align:
        aretomo_command.append('-Patch')
        aretomo_command.append(f'{n_patches_xy[0]}')
        aretomo_command.append(f'{n_patches_xy[1]}')

    if correct_tilt_angle_offset:
        aretomo_command.append('-TiltCor')
        aretomo_command.append('1')

    subprocess.run(aretomo_command)

    # Rename .tlt
    tlt_file_name = Path(f'{imod_directory}/{tilt_series_file.stem}_aln.tlt')
    new_tlt_stem = tlt_file_name.stem[:-4]
    new_output_name_tlt = Path(f'{imod_directory}/{new_tlt_stem}').with_suffix('.tlt')
    tlt_file_name.rename(new_output_name_tlt)


def find_binning_factor(
        pixel_size: float,
        target_pixel_size: float
) -> int:
    """Find closest power of two binning factor to reach target pixel size."""
    factors = 2 ** np.arange(7)
    binned_pixel_sizes = factors * pixel_size
    delta_pixel = np.abs(binned_pixel_sizes - target_pixel_size)
    binning = factors[np.argmin(delta_pixel)]
    return binning


def force_symlink(src: Path, link_name: Path):
    """Force creation of a symbolic link, removing any existing file."""
    if link_name.exists():
        os.remove(link_name)
    os.symlink(src, link_name)


def check_aretomo_availability():
    """Check for an installation of AreTomo on the PATH."""
    return shutil.which('AreTomo') is not None
