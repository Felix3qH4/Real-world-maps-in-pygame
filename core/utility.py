import math
from typing import List
import numpy
from core.models import Coordinate, TileBox


def tile_xy_from_lonlat(lon_deg: float, lat_deg: float, zoom: int) -> int:
  """
    Returns the X and Y value of the tile in the mercator grid projection matching the longitude and latitude.

    :param lon_deg [float] -- The longitude of a point
    :param lat_deg [float] -- The latitude of a point
    :param zoom [int] -- The desired zoom level

    :returns int, int -- The X and Y value of the tile in the mercator grid projection
  """
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  
  return xtile, ytile


def tile_top_left_lon_lat_from_xy(X: int, Y: int, zoom: int):
  """
    Returns the longitude and latitude of the top left corner of a tile.
    (Kind of an inverse function for 'core.utility.tile_xy_from_lonlat')
    (To get more latlon points, use 'core.utility.tile_corner_coordinates')

    :param X [int] -- The X value in the mercator grid projection
    :param Y [int] -- The Y value in the mercator grid projection
    :param zoom [int] -- The zoom value of the tile

    :returns core.models.Coordinate
  """
  n = 2 ** zoom
  lon_deg = X / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * Y / n)))
  lat_deg = lat_rad * 180.0 / math.pi

  return Coordinate(longitude = lon_deg, latitude = lat_deg)



def tile_corner_coordinates(X: int, Y: int, zoom: int):
  """
    Returns the coordinates (lon, lat) of the 4 corners of the tile and the center in the 'core.models.TileBox' template style.
    (Kind of an inverse function for 'core.utility.tile_xy_from_lonlat')

    :param X [int] -- The X value in the mercator grid projection
    :param Y [int] -- The Y value in the mercator grid projection
    :param zoom [int] -- The zoom value of the tile

    :returns core.models.TileBox

  """
  original_X, original_Y = X, Y
  out = []
  n = 2 ** zoom

  for i in range(5):
    if i == 1:
      X += 1
    elif i == 2:
      X += 1
      Y += 1
    elif i == 3:
      Y += 1
    elif i == 4:
      X += 0.5
      Y += 0.5

    lon_deg = X / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * Y / n)))
    lat_deg = lat_rad * 180.0 / math.pi

    out.append(Coordinate(longitude = lon_deg, latitude = lat_deg))

    X, Y = original_X, original_Y


  return TileBox(
    topleft = out[0],
    topright = out[1],
    bottomright = out[2],
    bottomleft = out[3],
    center = out[4]
  )



def latlng_from_px(px: int, py: int, corner_coordinates: TileBox, tilesize: int):
  """
    Returns the longitude and latitude of a given pixel in a raster tile.

    :param px [int] -- The x position of the pixel on the tile
    :param py [int] -- The y position of the pixel on the tile
    :param corner_coordinates [core.models.TileBox] -- The lon/lat of the corners and the center of the tile in a 'core.models.TileBox' template
    :param tilesize [int] -- The size of the tile (Tiles have to be of the same width and height)

    :returns core.models.Coordinate
  """

  ## Answer based on this Stackoverflow question:
  ## https://stackoverflow.com/a/13323592

  mapWidth = tilesize
  mapHeight = tilesize # assumes tile has same width and height

  mapLonLeft = corner_coordinates.bottomleft.longitude
  mapLonDelta = corner_coordinates.bottomright.longitude - mapLonLeft
  
  mapLatBottomRadian = math.radians(corner_coordinates.bottomleft.latitude)

  worldMapRadius = mapWidth / mapLonDelta * 360 / (2 * math.pi)
  mapOffsetY = (worldMapRadius / 2 * math.log((1 + math.sin(mapLatBottomRadian)) / (1 - math.sin(mapLatBottomRadian))))
  equatorY = mapHeight + mapOffsetY
  a = (equatorY - py) / worldMapRadius

  lat = 180 / math.pi * (2 * math.atan(math.exp(a)) - math.pi / 2)
  long = mapLonLeft + px / mapWidth * mapLonDelta

  return Coordinate(longitude = long, latitude = lat)




def px_from_latlng(lon: float, lat: float):
  ...




def shift(array, n, fill = 0):
    """
        Moves the values of an array to left/right.

        :param array [numpy.array] -- numpy array
        :param n [int] -- Move elements by n (negative number = move to the left)
        :param fill -- The value to fill the empty spots with

        :returns numpy.array

        From this answer:
            https://stackoverflow.com/questions/30399534/shift-elements-in-a-numpy-array
    """
    if array.ndim != 1: # array has more than 1 dimension
      e = shift_2d_array(array, n, fill)

    elif array.ndim == 1:
      e = numpy.empty_like(array)
      if n >= 0:
          e[:n] = fill
          e[n:] = array[:-n]
      else:
          e[n:] = fill
          e[:n] = array[-n:]
    
    return e


def shift_2d_array(array, n, fill=0):
  """
    Shifts an array of 2 dimensions.
  """
  t = numpy.empty_like(array)

  for i in range(array.ndim+1):
    t[i] = shift(array[i], n, fill)
    print(i)

  return t