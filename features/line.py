"""
    Author: Felix Michelis
    Date:   03/04/2023
            DD/MM/YYYY
"""

## A line feature which can be drawn on a map and saved as a geojson feature.

import pygame
from typing import List


class Line():
    def __init__(self, points: List[List[float]], color: str = "black", width: int = 2, visible: bool = True):
        """
            Draws a line on the map.
            The geojson representation can be called by the function 'to_geojson'.

            :param points [List[list]] -- The points of the line [[P1x, P1y], [P2x, P2y]]
            :param color [str] -- The color of the line
            :param width [int] -- The width of the line as an integer
            
            :param visible [bool] -- The visibility of the line (False = invisible, True = visible)

            :return None
        """
        #:param opacity [int] -- The opacity of the line (the lower, the less visible the line will be)
        
        self.points = points
        self.color = color
        self.width = width
        self.opacity: int = 1
        self.visible = visible

        self.feature_type = "LineString"
        self.window = pygame.display.get_surface()
    

    def draw(self):
        if self.visible:
            pygame.draw.lines(self.window, self.color, closed = False, points = self.points, width = self.width)
            

    def to_geojson(self):
        """ Returns a json object with itself in geojson format as feature. """
        geojson = {
            "type": "Feature",
            "properties": {
                "stroke": self.color, ################### NEEDS TO BE CONVERTED INTO HEX FROM RGBA
                "stroke-width": self.width,
                "stroke-opacity": self.opacity
            },
            "geometry": {
                "coordinates": self.points,
                "type": self.feature_type
            }
        }

        return geojson
        