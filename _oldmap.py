import numpy
import pygame
import math
from urllib.request import urlopen
import io

from core.models import MapConfig, Tile, Coordinate, Position
from core.utility import tile_xy_from_lonlat, tile_corner_coordinates, latlng_from_px

from concurrent import futures


class _Map():
    def __init__(self, mapconfig: MapConfig, debug_tileraster: bool = False) -> None:
        self.mapconfig: MapConfig = mapconfig
        self.mapconfig.tilesarray = numpy.zeros(
                (
                self.mapconfig.tilesarray_size,
                self.mapconfig.tilesarray_size
                ),
                dtype= Tile
            )

        ## +- center of the array minus loss by starting at the top left corner of the window
        self.mapconfig.array_x = int(self.mapconfig.tilesarray_size / 1.8)
        self.mapconfig.array_y = int(self.mapconfig.tilesarray_size / 1.8)
        
        self.mapconfig.x, self.mapconfig.y = tile_xy_from_lonlat(self.mapconfig.coordinates.longitude, self.mapconfig.coordinates.latitude, self.mapconfig.zoom)

        self.build_map()

        self.debug_tileraster = debug_tileraster

        tile : Tile = self.mapconfig.tilesarray[self.mapconfig.array_y, self.mapconfig.array_x]
        self.multiplier_X_tile = tile.x / self.mapconfig.array_x
        self.multiplier_Y_tile = tile.y / self.mapconfig.array_y

        self.multiplier_xcoord = tile.position.x / self.mapconfig.array_x
        self.multiplier_ycoord = tile.position.y / self.mapconfig.array_y

        self.add_position = None

        self.window = pygame.display.get_surface()
        self.w, self.h = self.window.get_width(), self.window.get_height()
        mx, my = math.ceil(self.w / self.mapconfig.tilesize), math.ceil(self.h / self.mapconfig.tilesize)

        self.narray = numpy.zeros((my, mx), dtype = Tile)
        self.carray = numpy.zeros((my, mx), dtype = Tile)
        

    def set_new_position(self, tile: Tile, position):
        tile.coordinates.x, tile.coordinates.y = position[0], position[1]

        return tile

    def add_to_position(self, tile: Tile, position=None):
        if isinstance(tile, Tile):
            if position == None:
                position = self.add_position

            tile.coordinates.x += position[0]
            tile.coordinates.y += position[1]

        return tile


    def build_map(self):
        window = pygame.display.get_surface()
        x_tiles = math.ceil(window.get_width() / self.mapconfig.tilesize)
        y_tiles = math.ceil(window.get_height() / self.mapconfig.tilesize)

        x = 0
        y = 0
        ## save the starting values of the array so we can add tiles next to them without modifying the initial starting position
        array_x = self.mapconfig.array_x
        array_y = self.mapconfig.array_y

        tile_x = self.mapconfig.x
        tile_y = self.mapconfig.y

        for i in range(y_tiles):
            for n in range(x_tiles):
                self.mapconfig.tilesarray[array_y, array_x] = self.create_tile(posx = x, posy = y, lx = tile_x, ly = tile_y)
                #print(array_x, array_y)
                #print(self.mapconfig.tilesarray[array_x, array_y])
                #print(tile_x, tile_y)
                x += self.mapconfig.tilesize
                array_x += 1
                tile_x += 1

            x = 0
            array_x = self.mapconfig.array_x
            tile_x = self.mapconfig.x
            tile_y += 1
            array_y += 1
            y += self.mapconfig.tilesize


    
    def create_tile(self, posx, posy, lx = None, ly = None):
        """
        :param posx -- The x position in the window
        :param posy -- The y position in the window
        :param lx -- The X value for the tile (in the url)
        :param ly -- The Y value for the tile (int the url)
        """
        print(lx, ly)
        if lx == None:
            lx = self.mapconfig.x
        if ly == None:
            ly = self.mapconfig.y

        
        zoom = self.mapconfig.zoom

        x, y = self.mapconfig.x, self.mapconfig.y
        self.mapconfig.x, self.mapconfig.y = lx, ly
        url_call = self.mapconfig.build_url()
        self.mapconfig.x, self.mapconfig.y = x, y

        image = self.fetch_tile(url_call)
        tile_image = pygame.image.load(image)
        tile_rect = pygame.Rect(posx, posy, tile_image.get_width(), tile_image.get_height())

        corner_coordinates = tile_corner_coordinates(lx, ly, self.mapconfig.zoom)

        new_tile = Tile(
            coordinates = Coordinate(
                longitude = corner_coordinates.topleft.longitude,
                latitude = corner_coordinates.topleft.latitude
            ),
            position = Position(
                x = posx,
                y = posy
            ),
            zoom = zoom,
            bearing = self.mapconfig.bearing,
            size = self.mapconfig.tilesize,
            url = url_call,
            image = tile_image,
            rect = tile_rect,
            x = lx,
            y = ly
        )


        return new_tile


    
    def fetch_tile(self, url):
        tile_str = urlopen(url).read()
        tile_image = io.BytesIO(tile_str)

        return tile_image


    def draw(self):
        window = pygame.display.get_surface()
        x_tiles = math.ceil(window.get_width() / self.mapconfig.tilesize)
        y_tiles = math.ceil(window.get_height() / self.mapconfig.tilesize)

        current_tilex = self.mapconfig.array_x
        current_tiley = self.mapconfig.array_y

        for i in range(y_tiles):
            for n in range(x_tiles):
                new_tile = self.mapconfig.tilesarray[current_tiley, current_tilex]
                print(new_tile)
                if isinstance(new_tile, Tile):
                    tile = new_tile
                    tile.rect = pygame.Rect(tile.position.x, tile.position.y, tile.size, tile.size)
                    #print(current_tilex, current_tiley)
                    #print(tile)
                    window.blit(tile.image, (tile.position.x, tile.position.y))

                    if self.debug_tileraster:
                        pygame.draw.rect(window, pygame.Color("black"), tile.rect, 1)
            
                else:
                    raise TypeError("Received integer to draw instead of Tile")


                current_tilex += 1
            
            current_tilex = self.mapconfig.array_x
            current_tiley += 1
    

    def add_to_array(self, rel):
        for y in self.mapconfig.tilesarray:
            for x in y:
                if isinstance(x, Tile):
                    x.position.x += rel[0]
                    x.position.y += rel[1]


    def on_drag(self, event_rel):

        event_relx, event_rely = event_rel[0], event_rel[1]
        a = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ]

        window = [
            [0, 1, 2],
            [0, 1, 2]
        ]

        if event_relx < 0: # moving left
            ...
        
        elif event_relx > 0: # moving right
            ...



    def on_drag(self, event_rel):
        #print(event_rel)
        self.add_position = event_rel
        
        self.add_to_array(event_rel)
        
        mult_x, mult_y = int(event_rel[0] / self.mapconfig.tilesize), int(event_rel[1] / self.mapconfig.tilesize)
        window = pygame.display.get_surface()
        width, height = window.get_width(), window.get_height()
        x_tiles, y_tiles = math.ceil(width / self.mapconfig.tilesize), math.ceil(height / self.mapconfig.tilesize)

        if event_rel[0] < 0: # moving left
            ...
        elif event_rel[0] > 0: # moving right
            ...

        if event_rel[1] < 0: # moving top
            ...
        elif event_rel[0] > 0: # moving bottom
            ...


            
        self.mapconfig.array_x += int(event_rel[0])
        self.mapconfig.array_y += int(event_rel[1])
        #tile : Tile = self.mapconfig.tilesarray[self.mapconfig.array_y, self.mapconfig.array_x]
        #self.multiplier_xcoord = tile.position.x / self.mapconfig.array_x
        #self.multiplier_ycoord = tile.position.y / self.mapconfig.array_y
        #print(self.mapconfig.array_x, self.mapconfig.array_y)

    
    def longitude_latitude_of_px(self, px: int, py: int):
        X, Y = 529, 349
        corner_coordinates = tile_corner_coordinates(X, Y, self.mapconfig.zoom)
        coordinates = latlng_from_px(px, py, corner_coordinates, self.mapconfig.tilesize)
        
        return coordinates