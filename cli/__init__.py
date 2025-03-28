#     Compress-py  A command-line interface for compressing files
#     Copyright (C) 2025  Yair Ziv
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import typer
import cli.rle
import cli.lzw
import cli.huffman
from typing import Optional
from cli.comparisons import compare_all

# The name of the app:
APP_NAME = "compress-py"


class CliApp:
    """
    A singleton wrapper of typer.Typer, representing the main app of the project.
    """
    __slots__ = (
        # The main typer.Typer object containing all commands:
        '__main_app',

        # The typer.Typer object responsible for compression:
        '__comp_app',

        # The typer.Typer object responsible for decompression:
        '__decomp_app'
    )

    __INSTANCE: Optional['CliApp'] = None

    def __new__(cls, app_name: str):
        # Ensure this is a singleton:
        if CliApp.__INSTANCE is None:
            CliApp.__INSTANCE = super().__new__(CliApp)
            CliApp.__INSTANCE.__init(app_name)
        return CliApp.__INSTANCE

    def __init(self, app_name: str) -> None:
        # Create all Typer objects:
        self.__main_app = typer.Typer(name=app_name, no_args_is_help=True, rich_markup_mode="rich")
        self.__comp_app = typer.Typer(name="compress", no_args_is_help=True, rich_markup_mode="rich")
        self.__decomp_app = typer.Typer(name="decompress", no_args_is_help=True, rich_markup_mode="rich")

        # Initialize the compress and decompress apps:
        self.__init_comp()
        self.__init_decomp()

        # Add the compare-all command:
        self.__main_app.command(no_args_is_help=True)(compare_all)

        # Add them to the main app:
        self.__main_app.add_typer(self.__comp_app)
        self.__main_app.add_typer(self.__decomp_app)

    def run(self):
        # Start the main app:
        self.__main_app()

    def __init_comp(self):
        # A tuple containing the different compression commands and their names:
        compression_algorithms = (
            (huffman.compress, "huffman"),
            (lzw.compress, "lzw"),
            (rle.compress, 'rle')
        )

        # Add the compression commands from the different files:
        for compressor, algo_name in compression_algorithms:
            self.__comp_app.command(name=algo_name, no_args_is_help=True)(compressor)

    def __init_decomp(self):
        # A tuple containing the different decompression commands:
        decompression_algorithms = (
            (huffman.decompress, "huffman"),
            (lzw.decompress, "lzw"),
            (rle.decompress, 'rle'),
        )

        # Add the decompression commands from the different files:
        for decompressor, algo_name in decompression_algorithms:
            self.__decomp_app.command(name=algo_name, no_args_is_help=True)(decompressor)
