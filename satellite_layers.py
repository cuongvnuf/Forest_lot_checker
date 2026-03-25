"""
Pre-configured satellite imagery sources for the 2020 forest plot survey include:
Sentinel-2 (Google Earth Engine) and publicly available satellite tiles.
"""

SATELLITE_SOURCES = {
    "Sentinel-2 2020 (Google Maps)": {
        "type": "xyz",
        "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "zmin": 0,
        "zmax": 21,
        "description": "Google satellite imagery (compiled over many years, high resolution)",
    },
    "Sentinel-2 2020 (ESRI World Imagery)": {
        "type": "xyz",
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "zmin": 0,
        "zmax": 19,
        "description": "ESRI World Imagery satellite imagery (regularly updated, high resolution)",
    },
    "Sentinel-2 2020 (Bing Maps)": {
        "type": "xyz",
        "url": "https://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1",
        "zmin": 0,
        "zmax": 19,
        "description": "Satellite Bing Maps",
        "tms": False,
    },
    "Sentinel-2 L2A (Copernicus Browser)": {
        "type": "xyz",
        "url": "https://sh.dataspace.copernicus.eu/ogc/wmts/43be0d69-7d28-4eb5-b6f9-0dc10b5b46b1?layer=TRUE-COLOR-S2L2A&style=default&tilematrixset=PopularWebMercator512&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fpng&TileMatrix={z}&TileCol={x}&TileRow={y}&TIME=2020-01-01/2020-12-31",
        "zmin": 0,
        "zmax": 14,
        "description": "Sentinel-2 L2A True Color (2020) from Copernicus Data Space",
    },
    "Google Earth Engine - Sentinel-2 2020": {
        "type": "wms",
        "url": "https://earthengine.googleapis.com/v1/projects/earthengine-legacy/maps/",
        "description": "Google Earth Engine API key is required (advanced option).",
        "disabled": True,
    },
}

DEFAULT_SATELLITE = "Sentinel-2 2020 (ESRI World Imagery)"

OSM_BASEMAP = {
    "name": "OpenStreetMap",
    "type": "xyz",
    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "zmin": 0,
    "zmax": 19,
}
