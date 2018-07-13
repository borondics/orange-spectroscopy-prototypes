import numpy as np

import Orange.data
from Orange.data.io import FileFormat

from orangecontrib.spectroscopy.data import _spectra_from_image
from orangecontrib.spectroscopy.preprocess import Cut

from .agilent import agilentMosaicTiles


def _as_table(spec_from_img):
    domvals, data, additional_table = spec_from_img
    data = np.asarray(data, dtype=np.float64)  # Orange assumes X to be float64
    features = [Orange.data.ContinuousVariable.make("%f" % f) for f in domvals]
    if additional_table is None:
        domain = Orange.data.Domain(features, None)
        return Orange.data.Table(domain, data)
    else:
        domain = Orange.data.Domain(features,
                                    class_vars=additional_table.domain.class_vars,
                                    metas=additional_table.domain.metas)
        ret_data = additional_table.transform(domain)
        ret_data.X = data
        return ret_data


class agilentMosaicTileReader(FileFormat):
    """ Tile-by-tile reader for Agilent FPA mosaic image files"""
    EXTENSIONS = ('.dmt',)
    DESCRIPTION = 'Agilent Mosaic Tile-by-tile'

    def preprocess(self, table):
        """
        replace with preprocessor chain input
        """
        cut = Cut(lowlim=2000, highlim=2006)
        return cut(table)


    def read(self):
        ret_table = None
        am = agilentMosaicTiles(self.filename)
        info = am.info
        tiles = am.tiles
        ytiles = am.tiles.shape[0]
        xtiles = am.tiles.shape[1]

        try:
            features = info['wavenumbers']
        except KeyError:
            #just start counting from 0 when nothing is known
            features = np.arange(X.shape[-1])

        try:
            px_size = info['FPA Pixel Size'] * info['PixelAggregationSize']
        except KeyError:
            # Use pixel units if FPA Pixel Size is not known
            px_size = 1

        for (x, y) in np.ndindex(tiles.shape):
            print(x,y)
            tile = tiles[x, y]()
            x_size, y_size = tile.shape[1], tile.shape[0]
            x_locs = np.linspace(x*x_size*px_size, (x+1)*x_size*px_size, num=x_size, endpoint=False)
            y_locs = np.linspace((ytiles-y-1)*y_size*px_size, (ytiles-y)*y_size*px_size, num=y_size, endpoint=False)

            tile_table = _as_table(_spectra_from_image(tile, features, x_locs, y_locs))
            tile_table = self.preprocess(tile_table)

            if ret_table is None:
                ret_table = tile_table
            else:
                ret_table.extend(tile_table)

        return ret_table