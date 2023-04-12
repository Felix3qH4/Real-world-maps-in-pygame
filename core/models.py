from pydantic import BaseModel
from typing import Any, List

from core.constants import (
    DEFAULT_TILESIZE,
    DEFAULT_ZOOM,
    DEFAULT_BEARING,
    DEFAULT_MAP_TILESARRAY_SIZE
)



class Coordinate(BaseModel):
    longitude: float
    latitude: float


class MapConfig(BaseModel):
    token: str
    coordinates: Coordinate
    zoom: int = DEFAULT_ZOOM
    bearing: int = DEFAULT_BEARING
    tilesize: int = DEFAULT_TILESIZE
    show_attribution: bool = False
    show_logo: bool = False
    ## Current X and Y coordinate of the tile
    x: int = None
    y: int = None
    ## Current X and Y position in the array
    array_x: int = None
    array_y: int = None
    url: str = "https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles"
    tilesarray_size: int = DEFAULT_MAP_TILESARRAY_SIZE
    tilesarray: list = None

    def build_url(self) -> str:
        """Returns the url string, only built here as we don't know some values at the start of the program"""
        return f"{self.url}/{self.tilesize}/{self.zoom}/{self.x}/{self.y}?access_token={self.token}"




class Position(BaseModel):
    x: int
    y: int


class ReferenceCoordinate(BaseModel):
    coordinate: Coordinate
    position: Position


class Tile(BaseModel):
    """
        :param coordinates [Coordinate] -- The coordinates of the top left corner of the tile
        :param position [Position] -- The position of the tile in the window
        :param zoom [int] -- The zoom level of the tile
        :param bearing [int] -- The bearing of the tile
        :param size [int] -- The size of the tile in the window (width = height)
        :param url [str] -- The url of the tile
        :param image -- The pygame.image.load() image of the tile
        :param rect -- A pygame.Rect()
        :param x [int] -- The X value on the world map raster
        :param y [int] -- The Y value on the world map raster
    """
    coordinates: Coordinate
    position: Position
    zoom: int
    bearing: int
    size: int
    url: str
    image: Any
    rect: Any
    x: int
    y: int
    #coord_topleft: ReferenceCoordinate
    #coord_topright: ReferenceCoordinate
    #coord_bottomleft: ReferenceCoordinate
    #coord_bottomright: ReferenceCoordinate
    #coord_center: ReferenceCoordinate

    def move_by(self, x: int, y: int) -> None:
        """
            Adds the x, y values to the position of the tile.

            :param x [int] -- The value to add to the x position of the tile in the window (can be negative)
            :param y [int] -- The value to add to the y position of the tile in the window (can be negative)
        """

        self.position.x += x
        self.position.y += y

    def set_position(self, x: int, y: int) -> None:
        """
            Set the position of the tile in the window.

            :param x [int] -- The x position of the tile in the window
            :param y [int] -- The y position of the tile in the window
        """

        self.position.x = x
        self.position.y = y



class TileBox(BaseModel):
    """
        Holds the longitude and latitude coordinates for each of the following points:
            - Top left (topleft)
            - Top right (topright)
            - Bottom right (bottomright)
            - Bottom left (bottomleft)
            - Center (center)
        
            In the following format:
                - corner.longitude, corner.latitude
                - 'topleft.longitude', 'topleft.latitude'
    """

    topleft: Coordinate
    topright: Coordinate
    bottomright: Coordinate
    bottomleft: Coordinate
    center: Coordinate


