"""
Các nguồn ảnh vệ tinh được cấu hình sẵn cho rà soát lô rừng năm 2020.
Bao gồm Sentinel-2 (Google Earth Engine) và các tile vệ tinh công khai.
"""

SATELLITE_SOURCES = {
    "Sentinel-2 2020 (Google Maps)": {
        "type": "xyz",
        "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "zmin": 0,
        "zmax": 21,
        "description": "Ảnh vệ tinh Google (tổng hợp nhiều năm, độ phân giải cao)",
    },
    "Sentinel-2 2020 (ESRI World Imagery)": {
        "type": "xyz",
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "zmin": 0,
        "zmax": 19,
        "description": "Ảnh vệ tinh ESRI World Imagery (cập nhật định kỳ, độ phân giải cao)",
    },
    "Sentinel-2 2020 (Bing Maps)": {
        "type": "xyz",
        "url": "https://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1",
        "zmin": 0,
        "zmax": 19,
        "description": "Ảnh vệ tinh Bing Maps",
        "tms": False,
    },
    "Sentinel-2 L2A (Copernicus Browser)": {
        "type": "xyz",
        "url": "https://sh.dataspace.copernicus.eu/ogc/wmts/43be0d69-7d28-4eb5-b6f9-0dc10b5b46b1?layer=TRUE-COLOR-S2L2A&style=default&tilematrixset=PopularWebMercator512&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fpng&TileMatrix={z}&TileCol={x}&TileRow={y}&TIME=2020-01-01/2020-12-31",
        "zmin": 0,
        "zmax": 14,
        "description": "Sentinel-2 L2A True Color (2020) từ Copernicus Data Space",
    },
    "Google Earth Engine - Sentinel-2 2020": {
        "type": "wms",
        "url": "https://earthengine.googleapis.com/v1/projects/earthengine-legacy/maps/",
        "description": "Cần API key Google Earth Engine (tùy chọn nâng cao)",
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
