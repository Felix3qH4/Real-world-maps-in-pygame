from tilemap import TileMap
import pygame as pg
import sys
from core.models import *

pg.init()

window = pg.display.set_mode((1500, 800))

m = TileMap(
    mapconfig = MapConfig(
        token = "pk.eyJ1IjoiM3FoNCIsImEiOiJjbGV1MjF4NGQxbHQzM3lwNGMxYTdnMzI1In0.7lG6JVMVyORtTipva7JsaQ",
        coordinates = Coordinate(
            longitude = 6.130083239353439,
            latitude = 49.607824632188226
        )
    ),
    debug_tileraster= True
)


clock = pg.time.Clock()

PRESSING = False

while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            sys.exit(0)
            pg.quit()

        if event.type == pg.MOUSEBUTTONDOWN:
            PRESSING = True
            pos = pg.mouse.get_pos()
            #print(m.longitude_latitude_of_px(pos[0], pos[1]))

        if event.type == pg.MOUSEBUTTONUP:
            PRESSING = False

        elif event.type == pg.MOUSEMOTION:
            if PRESSING:
                m.on_drag(event.rel)

    window.fill(pg.Color("black"))
    m.draw()
    pg.display.update()
    clock.tick(60)
    

pg.quit()