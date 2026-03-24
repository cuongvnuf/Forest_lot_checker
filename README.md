QGIS Plugin - Forest Plot Checker

A complete QGIS plugin allows you to:

Upload shapefiles containing forest plots (polygons)
Browse each plot sequentially by ID
Display Sentinel-2 or Planet 2020 satellite imagery as a background (via XYZ tile/WMS)
Automatically zoom to each plot being reviewed
Enter confirmation code: 0 (no forest) or 1 (forest present) for each plot
Save results to the shapefile's attribute fields
Navigation: previous plot / next plot / jump to any plot
Progress bar displaying review status
Input Data:

Load polygon shapefile directly from the computer
Automatically recognize existing polygon layers in QGIS
Optional plot ID field and result save field
Automatically create forest_rev field if not present
Background satellite imagery:

ESRI World Imagery (recommended - high resolution)
Google Maps Satellite
Sentinel-2 L2A True Color 2020 from Copernicus Data Space
Supports custom XYZ/WMS URLs (Planet, Google Earth Engine...)
Review Process:

Automatically browse plots 1 to N in order of ID
Automatic zoom and blinking of the plot being reviewed
Select result: 1 = Forest present or 0 = No forest present
Navigation: previous plot / next plot / jump to any plot
Save & Export Results:

Save directly to shapefile properties
Export results table to CSV file
Progress and statistics bar (reviewed / forest present / no forest present / not reviewed)
Author: cuongnt@vnuf.edu.vn
Trường Đại học Lâm nghiệp Việt Nam

