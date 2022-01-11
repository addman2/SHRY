#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=logging-fstring-interpolation, logging-not-lazy

# information
__author__ = "Genki Prayogo, and Kosuke Nakano"
__copyright__ = "Copyright (c) 2021-, The SHRY Project"
__credits__ = ["Genki Prayogo", "Kosuke Nakano"]

__license__ = "MIT"
__maintainer__ = "Genki Prayogo"
__email__ = "g.prayogo@icloud.com"
__date__ = "15. Nov. 2021"
__status__ = "Production"

"""Command line interface."""
import argparse
import datetime
import fnmatch
import logging

import tqdm

from . import const

# import sys


# Disable detailed stack trace.
# sys.excepthook = lambda t, e, _: print(f"{t.__name__}: {e}")


class TqdmLoggingHandler(logging.Handler):
    """
    Prevent logging from overwriting tqdm
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # pylint: disable=bare-except
            self.handleError(record)


def print_header():
    """
    Print header text
    """
    now = datetime.datetime.now()
    tz = now.astimezone().tzname()
    time_string = now.strftime("%c ") + tz
    bold = "\033[1m"
    end = "\033[0m"

    # logger.setLevel(logging.INFO)
    handler = TqdmLoggingHandler()
    handler.setLevel(logging.INFO)
    logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=[handler])
    logging.info("********************************\n")
    logging.info(
        f"SHRY: Suite for High-throughput generation of models"
        f"with atomic substitutions implemented by Python"
    )
    logging.info("\n********************************")
    logging.info("Begin " + time_string)


def print_footer():
    """
    Print footer text
    """
    now = datetime.datetime.now()
    tz = now.astimezone().tzname()
    time_string = now.strftime("%c ") + tz
    logging.info(const.HLINE)
    logging.info("Ends " + time_string)
    logging.info(const.HLINE)


def main():  # pylint: disable=missing-function-docstring
    parser = argparse.ArgumentParser(
        description="Quick use: `shry STRUCTURE_CIF`. See `shry -h` for more options.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # group = parser.add_argument_group("Input")
    parser.add_argument(
        "input",
        type=str,
        help=(
            "A CIF, or an `*.ini` containing command line options as keys.\n"
            "If using `*.ini`, write all keys under `DEFAULT` section "
            "(See `$SHRY_INSTALLDIR/examples`)"
        ),
    )

    group = parser.add_argument_group("structure modification")
    group.add_argument(
        "--from-species",
        "-f",
        nargs="*",
        type=str,
        help=(
            "Replace FROM_SPECIES from the CIF file into TO_SPECIES. "
            "Matches either `_atom_site_label` or `atom_site_type_symbol`. "
            "Use comma or space (preferred) for multiple substitutions."
        ),
        default=const.DEFAULT_FROM_SPECIES,
    )
    group.add_argument(
        "--to-species",
        "-t",
        nargs="*",
        type=str,
        help=(
            "Final chemical formula of the replaced FROM_SPECIES. "
            "Accepts various formats for the concentration and oxidation states "
            "such as SmFe12, Sm0.5Fe0.5, Sm3+Sm2+2Fe3, etc. "
            "The number of entry must be the same as FROM_SPECIES."
        ),
        default=const.DEFAULT_TO_SPECIES,
    )
    group.add_argument(
        "--scaling-matrix",
        "-s",
        nargs="*",
        type=str,  # To allow flexible separator
        help=(
            "Three or nine (for non-diagonal supercell) integers specifying "
            "the scaling matrix for constructing a supercell."
        ),
        default=const.DEFAULT_SCALING_MATRIX_STR,
    )

    group = parser.add_argument_group("input and output")
    group.add_argument(
        "--count-only",
        action="store_true",
        help=(
            "Enumerate the total number of ordered configurations "
            "from the given CIF and quit."
        ),
    )
    group.add_argument(
        "--mod-only",
        action="store_true",
        help="Write a modified CIF without generating the ordered structures.",
    )
    group.add_argument(
        "--no-write",
        action="store_true",
        help="Generate ordered structures, but do not store them into disk.",
    )
    group.add_argument(
        "--dir-size",
        type=int,
        default=const.DEFAULT_DIR_SIZE,
        help="Number of output CIFs written to each output directories.",
    )
    group.add_argument(
        "--sample",
        default=const.DEFAULT_SAMPLE,
        help="Write only SAMPLE CIFs from all ordered structures (random sampling).",
    )
    group.add_argument(
        "--write-symm",
        action="store_true",
        help="Write symmetries for all output CIFs (slower).",
    )
    group.add_argument(
        "--symmetrize",
        action="store_true",
        help=(
            "Use Wyckoff labels from a symmetry search to label the input CIF's sites. "
            "By default, the label given within the CIF is used."
        ),
    )

    group = parser.add_argument_group("run configuration")
    group.add_argument(
        "--symprec",
        type=float,
        default=const.DEFAULT_SYMPREC,
        help="Symmetry search precision (simulation cell fraction).",
    )
    group.add_argument(
        "--angle-tolerance",
        type=float,
        default=const.DEFAULT_ANGLE_TOLERANCE,
        help="Symmetry search angle tolerance (degrees).",
    )
    group.add_argument(
        "--disable-progressbar",
        action="store_true",
        help="Disable progress bar. May stabilize longer runs.",
    )
    group.add_argument(
        "--no-dmat",
        action="store_true",
        help="(devel/algo) Alternative algorithm without distance matrix (slower).",
    )
    group.add_argument(
        "--t-kind",
        default="sum",
        choices=("sum", "plsum", "det"),
        help=(
            "(devel/algo) Type of T function applied to "
            "distance matrix (sum, plsum, det)."
        ),
    )
    args = parser.parse_args()
    const.DISABLE_PROGRESSBAR = args.disable_progressbar

    # Print header first for faster perceived response
    print_header()

    # Late patch for count/mod/nowrite
    if args.count_only:
        args.no_write = True

    from .main import ScriptHelper  # pylint:disable=import-outside-toplevel

    if fnmatch.fnmatch(args.input, "*.ini"):
        # Note: when using *.ini, other arguments will be ignored.
        helper = ScriptHelper.from_file(args.input)
    else:
        # Trick to allow ",", ";", and whiteline as separator
        from_species = const.FLEXIBLE_SEPARATOR.split(",".join(args.from_species))
        to_species = const.FLEXIBLE_SEPARATOR.split(",".join(args.to_species))
        scaling_matrix = [
            int(x)
            for x in const.FLEXIBLE_SEPARATOR.split(",".join(args.scaling_matrix))
        ]
        from_species = list(filter(None, from_species))
        to_species = list(filter(None, to_species))
        scaling_matrix = list(filter(None, scaling_matrix))
        helper = ScriptHelper(
            structure_file=args.input,
            from_species=from_species,
            to_species=to_species,
            scaling_matrix=scaling_matrix,
            symmetrize=args.symmetrize,
            sample=args.sample,
            symprec=args.symprec,
            angle_tolerance=args.angle_tolerance,
            dir_size=args.dir_size,
            write_symm=args.write_symm,
            no_write=args.no_write,
            no_dmat=args.no_dmat,
            t_kind=args.t_kind,
        )
    helper.count()
    helper.save_modified_structure()
    if not args.count_only and not args.mod_only:
        helper.write()
    print_footer()

if __name__ == "__main__":
    main()
