import numpy
import pygame
import math
from urllib.request import urlopen
import io

from core.models import MapConfig, Tile, Coordinate, Position
from core.utility import tile_xy_from_lonlat, tile_corner_coordinates, latlng_from_px, shift

from concurrent import futures


class TileMap():
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

        self.window = pygame.display.get_surface()
        self.w, self.h = self.window.get_width(), self.window.get_height()
        self.mx, self.my = math.ceil(self.w / self.mapconfig.tilesize), math.ceil(self.h / self.mapconfig.tilesize)

        self.narray = numpy.zeros((self.my+2, self.mx+2), dtype = Tile) # +2 to cover if one tile is a bit over the edge and we already have to draw the next one
        

        self.build_map()

        self.debug_tileraster = debug_tileraster

        self.add_position = None

        print(self.narray)

        
    


    def build_map(self):
        x = 0
        y = 0
        
        array_x = 1
        array_y = 1

        tile_x = self.mapconfig.x
        tile_y = self.mapconfig.y

        th = {}

        for i in range(self.my):
            for n in range(self.mx):
                #self.narray[array_y, array_x] = self.create_tile(posx = x, posy = y, lx = tile_x, ly = tile_y)
                th[(array_y, array_x)] = [x, y, tile_x, tile_y]
                x += self.mapconfig.tilesize
                array_x += 1
                tile_x += 1

            x = 0
            array_x = 1
            tile_x = self.mapconfig.x
            tile_y += 1
            array_y += 1
            y += self.mapconfig.tilesize


        for i in range(len(th)):
            executor = futures.ThreadPoolExecutor(20)
            fut = [executor.submit(self.create_tile_thread, tile[0], tile[1], th[tile][0], th[tile][1], th[tile][2], th[tile][3]) for tile in th]
            

    def create_tile_thread(self, array_y, array_x, posx, posy, lx = None, ly = None):
        self.narray[array_y, array_x] = self.create_tile(posx, posy, lx, ly)


    def create_tile(self, posx, posy, lx = None, ly = None):
        """
        :param posx -- The x position in the window
        :param posy -- The y position in the window
        :param lx -- The X value for the tile (in the url)
        :param ly -- The Y value for the tile (int the url)
        """
        
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
        window = self.window
        # XXX Check for window resize

        current_tilex = 0
        current_tiley = 0

        
        for row in self.narray:
            for t in self.narray[0]:
                new_tile = self.narray[current_tiley, current_tilex]
                if isinstance(new_tile, Tile):
                    tile = new_tile
                    tile.rect = pygame.Rect(tile.position.x, tile.position.y, tile.size, tile.size)
                    self.narray[current_tiley, current_tilex] = tile
                    window.blit(tile.image, (tile.position.x, tile.position.y))

                    if self.debug_tileraster:
                        pygame.draw.rect(window, pygame.Color("black"), tile.rect, 1)
            
                else:
                    #raise TypeError("Received integer to draw instead of Tile")
                    ## XXX Draw a black rectangle maybe or is this covered by black background?
                    pass


                current_tilex += 1
            
            current_tilex = 0
            current_tiley += 1



    
    def longitude_latitude_of_px(self, px: int, py: int):
        x, y = 0, 0
        X, Y = None, None
        for row in self.narray:
            for obj in self.narray:
                tile = self.narray[y, x]
                if isinstance(tile, Tile):
                    if tile.rect.collidepoint(px, py):
                        X = tile.x
                        Y = tile.y
                        px, py = px - tile.position.x, py - tile.position.y
                        break
                x += 1
            x = 0
            y += 1

        if X == None or Y == None:
            raise ValueError("No value found for X and Y! Did the user click on a tile?")
        
        corner_coordinates = tile_corner_coordinates(X, Y, self.mapconfig.zoom)
        coordinates = latlng_from_px(px, py, corner_coordinates, self.mapconfig.tilesize)
        
        return coordinates
    




    def on_drag(self, event_rel):
        """
            This function is called when the user drags around the map.
            It updates the position of the tiles accordingly and loads new tiles if necessary.

            :param event_rel [tuple] -- The movement on the x and the y axis Tuple(x, y)

            :return None -- updates the position of the tiles and loads new ones if necessary
        """
        relx, rely = event_rel[0], event_rel[1]
        window = pygame.display.get_surface()
        window_w, window_h = window.get_width(), window.get_height()

        #new_tiles = {} usage not possible -> see relx < 0 -> if not isinstance(..., Tile)

        ## Update the position of all current tiles
        for y, row in enumerate(self.narray, 0):
            for x, t in enumerate(row, 0):
                tile = self.narray[y, x]
                if isinstance(tile, Tile):
                    tile.move_by(relx, rely)


        if relx < 0: # map moves to the left ( = user goes to the right)
            ## If there has not already been a tile added to the right side of the array
            if not isinstance(self.narray[0, len(self.narray[0])-1], Tile): # the last value on the right side
                nax, nay = len(self.narray[0]) - 2, 1
                reftile = self.narray[nay, nax]
                if isinstance(reftile, Tile):
                    ## If the tile does not cover the entire window
                    if reftile.position.x + self.mapconfig.tilesize < window_w:
                        i = -1 ## This differs from the elif statement under this one as here we want to add a tile to the top right corner too, which is already done in the
                        ## next statement so there we draw based on that top tile (we are always drawing based on the most upper tile in the array)
                        topx, topy = len(self.narray[0])-1, 0

                        for row in self.narray:
                            self.narray[topy, topx] = self.create_tile(reftile.position.x + self.mapconfig.tilesize, reftile.position.y + (i * self.mapconfig.tilesize), reftile.x + 1, reftile.y + i)
                            ## We cannot use the futures.ThreadPoolExecutor as this would allow moving around the map while images are being loaded
                            ## problem with this is that we would load an image and during the loading time, the user continues moving around so that the position
                            ## at which the tile is then displayed does no longer match the position it should be because the user continued moving so we would have
                            ## to save the movement inbetween the start of the load time and the end of the load time to then add it to the position of the tile

                            #new_tiles[(topy, topx)] = [reftile.position.x + self.mapconfig.tilesize + relx, reftile.position.y + (i * self.mapconfig.tilesize), reftile.x + 1, reftile.y + i]
                            i += 1
                            topy += 1

            ## If there has already been added a tile to the right side of the array
            ## we will have to move the entire content of the array to the left by one place
            elif isinstance(self.narray[0, len(self.narray[0]) -1], Tile):
                nax, nay = len(self.narray[0]) - 1, 0
                reftile = self.narray[nay, nax]
                
                if reftile.position.x + self.mapconfig.tilesize < window_w:
                    self.narray = shift(self.narray, -1, fill=0)
                    i = 0
                    topx, topy = len(self.narray[0])-1, 0

                    for row in self.narray:
                        self.narray[topy, topx] = self.create_tile(reftile.position.x + self.mapconfig.tilesize, reftile.position.y + (i * self.mapconfig.tilesize), reftile.x + 1, reftile.y + i)
                        ## See above to know why the next line is commented out
                        #new_tiles[(topy, topx)] = [reftile.position.x + self.mapconfig.tilesize + relx, reftile.position.y + (i * self.mapconfig.tilesize), reftile.x + 1, reftile.y + i]
                        i += 1
                        topy += 1

        elif relx > 0:
            reftile = self.narray[0, 0]

            if not isinstance(reftile, Tile):
                nax, nay = 1, 1
                reftile = self.narray[nay, nax]

                if reftile.position.x > 0:
                    i = -1
                    topx, topy = 0, 0

                    for row in self.narray:
                        self.narray[topy, topx] = self.create_tile(reftile.position.x - self.mapconfig.tilesize, reftile.position.y + (i * self.mapconfig.tilesize), reftile.x - 1, reftile.y + i)
                        i += 1
                        topy += 1

            if isinstance(reftile, Tile):
                if reftile.position.x > 0:
                    self.narray = shift(self.narray, 1, fill = 0)
                    i = 0
                    topx, topy = 0, 0

                    for row in self.narray:
                        self.narray[topy, topx] = self.create_tile(reftile.position.x - self.mapconfig.tilesize, reftile.position.y + (i * self.mapconfig.tilesize), reftile.x - 1, reftile.y + i)
                        i += 1
                        topy += 1
                    


        if rely < 0: # dragging the tiles up

            reftile = self.narray[len(self.narray)-1, 0]

            if not isinstance(reftile, Tile):
                nax, nay = 1, len(self.narray) - 2
                reftile = self.narray[nay, nax]

                if reftile.position.y + self.mapconfig.tilesize < window_h:
                    i = -1
                    topx, topy = 0, len(self.narray)-1

                    for tile in self.narray[topy]:
                        self.narray[topy, topx] = self.create_tile(reftile.position.x + (i * self.mapconfig.tilesize), reftile.position.y + self.mapconfig.tilesize, reftile.x + i, reftile.y + 1)
                        i += 1
                        topx += 1

            if isinstance(reftile, Tile):
                if reftile.position.y + self.mapconfig.tilesize < window_h:
                    rot_array = numpy.rot90(self.narray, k=1, axes=(1, 0)) # rotate clockwise one time
                    shift_array = shift(rot_array, 1, fill = 0)
                    self.narray = numpy.rot90(shift_array, k=-1, axes=(1, 0))
                    i = 0
                    topx, topy = 0, len(self.narray)-1

                    for tile in self.narray[topy]:
                        self.narray[topy, topx] = self.create_tile(reftile.position.x + (i * self.mapconfig.tilesize), reftile.position.y + self.mapconfig.tilesize, reftile.x + i, reftile.y + 1)
                        i += 1
                        topx += 1

        elif rely > 0:
            reftile = self.narray[0, 0]

            if not isinstance(reftile, Tile):
                reftile = self.narray[1, 1]

                if reftile.position.y > 0:
                    topx, topy = 0, 0
                    for i, tile in enumerate(self.narray[topy], -1):
                        self.narray[topy, topx] = self.create_tile(reftile.position.x + (i*self.mapconfig.tilesize), reftile.position.y-self.mapconfig.tilesize, reftile.x + i, reftile.y - 1)
                        topx += 1


        ## this is not possible, see the first if statement for why not
        #for tile in new_tiles:
            #executor = futures.ThreadPoolExecutor(20)
            #fut = [executor.submit(self.create_tile_thread, tile[0], tile[1], new_tiles[tile][0], new_tiles[tile][1], new_tiles[tile][2], new_tiles[tile][3]) for tile in new_tiles]

        
        
