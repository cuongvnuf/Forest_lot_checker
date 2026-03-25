import os
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QGroupBox,
    QProgressBar, QFileDialog, QMessageBox, QRadioButton,
    QButtonGroup, QFrame, QSizePolicy, QToolButton, QLineEdit,
    QTextEdit, QSplitter, QWidget, QCheckBox
)
from qgis.PyQt.QtCore import Qt, QSettings, pyqtSignal
from qgis.PyQt.QtGui import QFont, QColor, QPalette

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsMapLayer,
    QgsFeatureRequest, QgsField, QgsFields, QgsExpression,
    QgsFeature, QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsRectangle, QgsVectorFileWriter, QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant, QDateTime

from .satellite_layers import SATELLITE_SOURCES, DEFAULT_SATELLITE, OSM_BASEMAP


class ForestReviewDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.current_layer = None
        self.features = []
        self.current_index = 0
        self.review_field = "forest_rev"
        self.id_field = None
        self.satellite_layer = None
        self.basemap_layer = None
        self.settings = QSettings("ForestReview", "ForestReviewPlugin")

        self.setWindowTitle("Forest Plot Checker")
        self.setMinimumWidth(520)
        self.setMinimumHeight(650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._build_ui()
        self._load_layers_combo()
        self._restore_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("REVIEW THE CURRENT STATUS FOREST")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1a5c1a; padding: 5px;")
        main_layout.addWidget(title_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(sep)

        layer_group = QGroupBox("1. Select data layer")
        layer_layout = QGridLayout(layer_group)

        layer_layout.addWidget(QLabel("Layer polygon:"), 0, 0)
        self.layer_combo = QComboBox()
        self.layer_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layer_combo.currentIndexChanged.connect(self._on_layer_changed)
        layer_layout.addWidget(self.layer_combo, 0, 1)

        load_btn = QPushButton("Add layer...")
        load_btn.setToolTip("Download the shapefile from your computer.")
        load_btn.clicked.connect(self._load_shapefile)
        layer_layout.addWidget(load_btn, 0, 2)

        layer_layout.addWidget(QLabel("Field ID of lot:"), 1, 0)
        self.id_field_combo = QComboBox()
        self.id_field_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layer_layout.addWidget(self.id_field_combo, 1, 1, 1, 2)

        layer_layout.addWidget(QLabel("Result:"), 2, 0)
        self.result_field_combo = QComboBox()
        self.result_field_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.result_field_combo.setToolTip("Select the field to save the review results (0/1). A new field can be created.")
        layer_layout.addWidget(self.result_field_combo, 2, 1)

        self.create_field_btn = QPushButton("Create new field")
        self.create_field_btn.clicked.connect(self._create_review_field)
        layer_layout.addWidget(self.create_field_btn, 2, 2)

        main_layout.addWidget(layer_group)

        satellite_group = QGroupBox("2. Satellite image (2020)")
        satellite_layout = QGridLayout(satellite_group)

        satellite_layout.addWidget(QLabel("Image source:"), 0, 0)
        self.satellite_combo = QComboBox()
        for name, info in SATELLITE_SOURCES.items():
            if not info.get("disabled", False):
                self.satellite_combo.addItem(name)
        default_idx = self.satellite_combo.findText(DEFAULT_SATELLITE)
        if default_idx >= 0:
            self.satellite_combo.setCurrentIndex(default_idx)
        satellite_layout.addWidget(self.satellite_combo, 0, 1)

        self.add_satellite_btn = QPushButton("Add to map")
        self.add_satellite_btn.clicked.connect(self._add_satellite_layer)
        satellite_layout.addWidget(self.add_satellite_btn, 0, 2)

        self.custom_url_check = QCheckBox("URL optional (XYZ/WMS):")
        self.custom_url_check.toggled.connect(self._toggle_custom_url)
        satellite_layout.addWidget(self.custom_url_check, 1, 0, 1, 3)

        self.custom_url_edit = QLineEdit()
        self.custom_url_edit.setPlaceholderText(
            "https://... or wms://url?layers=...&styles=...&..."
        )
        self.custom_url_edit.setEnabled(False)
        satellite_layout.addWidget(self.custom_url_edit, 2, 0, 1, 3)

        sat_info_label = QLabel(
         "Hint: Use ESRI World Imagery or Google Maps to view the most recent satellite imagery."
          "To view the exact Sentinel-2 image for 2020, log in to Copernicus Data Space."
        )
        sat_info_label.setWordWrap(True)
        sat_info_label.setStyleSheet("color: #555; font-size: 9pt;")
        satellite_layout.addWidget(sat_info_label, 3, 0, 1, 3)

        main_layout.addWidget(satellite_group)

        init_group = QGroupBox("3. Start the review")
        init_layout = QHBoxLayout(init_group)

        self.start_btn = QPushButton("START")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #1a5c1a; color: white; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #247324; }"
            "QPushButton:disabled { background-color: #aaa; }"
        )
        self.start_btn.clicked.connect(self._start_review)
        init_layout.addWidget(self.start_btn)

        self.total_label = QLabel("Total of lots: -")
        self.total_label.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(self.total_label)

        main_layout.addWidget(init_group)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(sep2)

        review_group = QGroupBox("4. Review each forest lot.")
        review_layout = QVBoxLayout(review_group)

        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("Current lot:"), 0, 0)
        self.current_id_label = QLabel("-")
        self.current_id_label.setFont(QFont("", 11, QFont.Bold))
        self.current_id_label.setStyleSheet("color: #1a3c8a;")
        info_layout.addWidget(self.current_id_label, 0, 1)

        info_layout.addWidget(QLabel("Position:"), 0, 2)
        self.position_label = QLabel("-/-")
        self.position_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.position_label, 0, 3)

        info_layout.addWidget(QLabel("Present results:"), 1, 0)
        self.current_result_label = QLabel("-")
        self.current_result_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.current_result_label, 1, 1)

        info_layout.addWidget(QLabel("Area:"), 1, 2)
        self.area_label = QLabel("-")
        self.area_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.area_label, 1, 3)

        review_layout.addLayout(info_layout)

        verdict_frame = QFrame()
        verdict_frame.setFrameShape(QFrame.StyledPanel)
        verdict_frame.setStyleSheet("background-color: #f0f8f0; border-radius: 6px; padding: 5px;")
        verdict_layout = QVBoxLayout(verdict_frame)

        verdict_title = QLabel("Confirmation results:")
        verdict_title.setFont(QFont("", 10, QFont.Bold))
        verdict_layout.addWidget(verdict_title)

        radio_layout = QHBoxLayout()
        self.verdict_group = QButtonGroup(self)

        self.radio_forest = QRadioButton("1 - FOREST")
        self.radio_forest.setStyleSheet(
            "QRadioButton { color: #1a5c1a; font-weight: bold; font-size: 11pt; padding: 5px 15px; }"
            "QRadioButton::indicator { width: 18px; height: 18px; }"
        )
        self.verdict_group.addButton(self.radio_forest, 1)
        radio_layout.addWidget(self.radio_forest)

        self.radio_no_forest = QRadioButton("0 - NON-FOREST")
        self.radio_no_forest.setStyleSheet(
            "QRadioButton { color: #8b0000; font-weight: bold; font-size: 11pt; padding: 5px 15px; }"
            "QRadioButton::indicator { width: 18px; height: 18px; }"
        )
        self.verdict_group.addButton(self.radio_no_forest, 0)
        radio_layout.addWidget(self.radio_no_forest)

        self.radio_unclear = QRadioButton("? - Undetermined")
        self.radio_unclear.setStyleSheet(
            "QRadioButton { color: #666; font-size: 10pt; padding: 5px 15px; }"
        )
        self.verdict_group.addButton(self.radio_unclear, -1)
        radio_layout.addWidget(self.radio_unclear)

        verdict_layout.addLayout(radio_layout)
        review_layout.addWidget(verdict_frame)

        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("← Previous lot")
        self.prev_btn.setMinimumHeight(34)
        self.prev_btn.setStyleSheet(
            "QPushButton { background-color: #4a7fb5; color: white; border-radius: 4px; }"
            "QPushButton:hover { background-color: #5a90c6; }"
            "QPushButton:disabled { background-color: #aaa; }"
        )
        self.prev_btn.clicked.connect(self._go_prev)
        nav_layout.addWidget(self.prev_btn)

        self.save_next_btn = QPushButton("Save & Next lot →")
        self.save_next_btn.setMinimumHeight(34)
        self.save_next_btn.setStyleSheet(
            "QPushButton { background-color: #1a5c1a; color: white; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #247324; }"
            "QPushButton:disabled { background-color: #aaa; }"
        )
        self.save_next_btn.clicked.connect(self._save_and_next)
        nav_layout.addWidget(self.save_next_btn)

        review_layout.addLayout(nav_layout)

        jump_layout = QHBoxLayout()
        jump_layout.addWidget(QLabel("Go to number:"))
        self.jump_spin = QSpinBox()
        self.jump_spin.setMinimum(1)
        self.jump_spin.setMaximum(999999)
        jump_layout.addWidget(self.jump_spin)
        jump_btn = QPushButton("Đến")
        jump_btn.clicked.connect(self._jump_to)
        jump_layout.addWidget(jump_btn)
        jump_layout.addStretch()

        self.zoom_btn = QPushButton("Zoom current lot")
        self.zoom_btn.clicked.connect(self._zoom_to_current)
        jump_layout.addWidget(self.zoom_btn)

        review_layout.addLayout(jump_layout)

        main_layout.addWidget(review_group)

        progress_group = QGroupBox("5. Work progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 2px solid #aaa; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #1a5c1a; border-radius: 3px; }"
        )
        progress_layout.addWidget(self.progress_bar)

        stats_layout = QHBoxLayout()
        self.reviewed_label = QLabel("Checked: 0")
        self.forest_label = QLabel("Forest: 0")
        self.forest_label.setStyleSheet("color: #1a5c1a; font-weight: bold;")
        self.no_forest_label = QLabel("Non Forest: 0")
        self.no_forest_label.setStyleSheet("color: #8b0000; font-weight: bold;")
        self.remaining_label = QLabel("Not yet reviewed: 0")
        stats_layout.addWidget(self.reviewed_label)
        stats_layout.addWidget(self.forest_label)
        stats_layout.addWidget(self.no_forest_label)
        stats_layout.addWidget(self.remaining_label)
        progress_layout.addLayout(stats_layout)

        main_layout.addWidget(progress_group)

        save_layout = QHBoxLayout()
        self.save_all_btn = QPushButton("Save all by shapefile")
        self.save_all_btn.setStyleSheet(
            "QPushButton { background-color: #8b6914; color: white; border-radius: 4px; padding: 5px 10px; }"
            "QPushButton:hover { background-color: #a07a1a; }"
        )
        self.save_all_btn.clicked.connect(self._save_all)
        save_layout.addWidget(self.save_all_btn)

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self._export_csv)
        save_layout.addWidget(self.export_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        save_layout.addWidget(self.close_btn)

        main_layout.addLayout(save_layout)

        self._set_review_enabled(False)

    def _toggle_custom_url(self, checked):
        self.custom_url_edit.setEnabled(checked)
        self.satellite_combo.setEnabled(not checked)

    def _set_review_enabled(self, enabled):
        self.radio_forest.setEnabled(enabled)
        self.radio_no_forest.setEnabled(enabled)
        self.radio_unclear.setEnabled(enabled)
        self.prev_btn.setEnabled(enabled)
        self.save_next_btn.setEnabled(enabled)
        self.jump_spin.setEnabled(enabled)
        self.zoom_btn.setEnabled(enabled)
        self.save_all_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)

    def _load_layers_combo(self):
        self.layer_combo.clear()
        self.layer_combo.addItem("-- Select layer--", None)
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.layer_combo.addItem(layer.name(), layer.id())

    def _on_layer_changed(self, index):
        layer_id = self.layer_combo.currentData()
        if layer_id is None:
            self.current_layer = None
            self.id_field_combo.clear()
            self.result_field_combo.clear()
            return

        layer = QgsProject.instance().mapLayer(layer_id)
        if layer and isinstance(layer, QgsVectorLayer):
            self.current_layer = layer
            self._populate_field_combos()

    def _populate_field_combos(self):
        if not self.current_layer:
            return
        fields = self.current_layer.fields()
        self.id_field_combo.clear()
        self.result_field_combo.clear()

        for field in fields:
            self.id_field_combo.addItem(field.name())
            self.result_field_combo.addItem(field.name())

        for i in range(self.id_field_combo.count()):
            fname = self.id_field_combo.itemText(i).lower()
            if fname in ("id", "fid", "objectid", "lot_id", "ma_lo", "id_lo"):
                self.id_field_combo.setCurrentIndex(i)
                break

        for i in range(self.result_field_combo.count()):
            fname = self.result_field_combo.itemText(i).lower()
            if fname in ("forest_rev", "review", "detail", "result", "forest"):
                self.result_field_combo.setCurrentIndex(i)
                break

    def _load_shapefile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a file shapefile", "",
            "Shapefile (*.shp);;All file (*.*)"
        )
        if not file_path:
            return

        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        layer = QgsVectorLayer(file_path, layer_name, "ogr")

        if not layer.isValid():
            QMessageBox.critical(self, "Error", f"Unable to load file:\n{file_path}")
            return

        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            QMessageBox.warning(
                self, "Warning",
                "The selected file is not a polygon. Please select a polygon shapefile for the forest plot."
            )
            return

        QgsProject.instance().addMapLayer(layer)
        self._load_layers_combo()

        for i in range(self.layer_combo.count()):
            if self.layer_combo.itemData(i) == layer.id():
                self.layer_combo.setCurrentIndex(i)
                break

        self.iface.mapCanvas().setExtent(layer.extent())
        self.iface.mapCanvas().refresh()

    def _create_review_field(self):
        if not self.current_layer:
            QMessageBox.warning(self, "Warning", "Please select a data layer")
            return

        field_name = "forest_rev"
        fields = self.current_layer.fields()
        if fields.indexOf(field_name) >= 0:
            QMessageBox.information(
                self, "Notification",
                f"Field '{field_name}' It already exists in the data layer."
            )
            for i in range(self.result_field_combo.count()):
                if self.result_field_combo.itemText(i) == field_name:
                    self.result_field_combo.setCurrentIndex(i)
                    break
            return

        self.current_layer.startEditing()
        new_field = QgsField(field_name, QVariant.Int)
        self.current_layer.addAttribute(new_field)
        self.current_layer.commitChanges()

        self._populate_field_combos()

        for i in range(self.result_field_combo.count()):
            if self.result_field_combo.itemText(i) == field_name:
                self.result_field_combo.setCurrentIndex(i)
                break

        QMessageBox.information(
            self, "Successful",
            f"Field created '{field_name}' in your data.\n"
            "This field will store the scan results (0= non-forest, 1=forest)."
        )

    def _add_satellite_layer(self):
        if self.custom_url_check.isChecked():
            url = self.custom_url_edit.text().strip()
            if not url:
                QMessageBox.warning(self, "Warning", "Please enter URL satellite image.")
                return
            layer_name = "Optional satellite imagery"
            uri = f"type=xyz&url={url}&zmin=0&zmax=21"
        else:
            source_name = self.satellite_combo.currentText()
            source = SATELLITE_SOURCES.get(source_name)
            if not source:
                return
            layer_name = source_name
            if source["type"] == "xyz":
                url = source["url"]
                zmin = source.get("zmin", 0)
                zmax = source.get("zmax", 19)
                uri = f"type=xyz&url={url}&zmin={zmin}&zmax={zmax}"
            elif source["type"] == "wms":
                QMessageBox.information(
                    self, "Information",
                    "This WMS image source requires further configuration.\n"
                    "Please add it manually in QGIS > Layer > Add Layer > Add WMS/WMTS Layer."
                )
                return
            else:
                return

        existing = self._find_existing_layer(layer_name)
        if existing:
            reply = QMessageBox.question(
                self, "This field already exists.",
                f"Field '{layer_name}' It's already on the map. Continue adding?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        satellite_layer = QgsRasterLayer(uri, layer_name, "wms")
        if not satellite_layer.isValid():
            QMessageBox.warning(
                self, "Connection error",
                f"Unable to connect to image source:\n{source_name}\n\n"
                "Check your network connection and try again. Or choose a different image source."
            )
            return

        root = QgsProject.instance().layerTreeRoot()
        QgsProject.instance().addMapLayer(satellite_layer, False)
        root.insertLayer(len(root.children()), satellite_layer)
        self.satellite_layer = satellite_layer

        self.iface.mapCanvas().refresh()
        QMessageBox.information(
            self, "Thành công",
            f"Satellite imagery layer added.:\n'{layer_name}'\n\n"
            "The image layer is placed at the bottom so as not to obscure the forest plot."
        )

    def _find_existing_layer(self, name):
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == name:
                return layer
        return None

    def _start_review(self):
        if not self.current_layer:
            QMessageBox.warning(self, "Warning", "Please select the forest lot first.")
            return

        id_field = self.id_field_combo.currentText()
        result_field = self.result_field_combo.currentText()

        if not id_field:
            QMessageBox.warning(self, "Warning", "Please select the forest lot ID field.")
            return

        if not result_field:
            reply = QMessageBox.question(
                self, "No field result",
                "Field for saving results not selected. Automatically create field 'forest_rev'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._create_review_field()
                result_field = "forest_rev"
            else:
                return

        self.id_field = id_field
        self.review_field = result_field

        request = QgsFeatureRequest()
        request.addOrderBy(id_field, ascending=True)
        self.features = list(self.current_layer.getFeatures(request))

        if not self.features:
            QMessageBox.warning(self, "Warning", "The data layer contains no objects.")
            return

        self.current_index = 0
        total = len(self.features)
        self.total_label.setText(f"Total lot: {total}")
        self.jump_spin.setMaximum(total)
        self.progress_bar.setMaximum(total)

        self._set_review_enabled(True)
        self._display_current_feature()
        self._update_stats()

        self.start_btn.setText("RESTART")

    def _display_current_feature(self):
        if not self.features:
            return

        if self.current_index < 0:
            self.current_index = 0
        if self.current_index >= len(self.features):
            self.current_index = len(self.features) - 1

        feature = self.features[self.current_index]
        total = len(self.features)

        id_val = feature[self.id_field] if self.id_field else str(feature.id())
        self.current_id_label.setText(f"Lot #{id_val}")
        self.position_label.setText(f"{self.current_index + 1} / {total}")
        self.jump_spin.setValue(self.current_index + 1)

        geom = feature.geometry()
        if geom:
            area = geom.area()
            if area < 10000:
                area_text = f"{area:.2f} m²"
            else:
                area_text = f"{area / 10000:.4f} ha"
            self.area_label.setText(area_text)
        else:
            self.area_label.setText("-")

        result_val = feature[self.review_field] if self.review_field in [f.name() for f in self.current_layer.fields()] else None

        self.verdict_group.setExclusive(False)
        self.radio_forest.setChecked(False)
        self.radio_no_forest.setChecked(False)
        self.radio_unclear.setChecked(False)
        self.verdict_group.setExclusive(True)

        if result_val == 1:
            self.radio_forest.setChecked(True)
            self.current_result_label.setText("FOREST (1)")
            self.current_result_label.setStyleSheet("color: #1a5c1a; font-weight: bold;")
        elif result_val == 0:
            self.radio_no_forest.setChecked(True)
            self.current_result_label.setText("NON-FOREST (0)")
            self.current_result_label.setStyleSheet("color: #8b0000; font-weight: bold;")
        else:
            self.radio_unclear.setChecked(True)
            self.current_result_label.setText("Undetermined")
            self.current_result_label.setStyleSheet("color: #666; font-weight: bold;")

        self._zoom_to_current()
        self._highlight_current_feature(feature)

    def _zoom_to_current(self):
        if not self.features or self.current_index >= len(self.features):
            return

        feature = self.features[self.current_index]
        geom = feature.geometry()
        if not geom:
            return

        canvas_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        layer_crs = self.current_layer.crs()

        if canvas_crs != layer_crs:
            transform = QgsCoordinateTransform(layer_crs, canvas_crs, QgsProject.instance())
            geom.transform(transform)

        rect = geom.boundingBox()
        scale_factor = 1.5
        width = rect.width() * scale_factor
        height = rect.height() * scale_factor
        center = rect.center()

        buffered = QgsRectangle(
            center.x() - width / 2,
            center.y() - height / 2,
            center.x() + width / 2,
            center.y() + height / 2,
        )

        self.iface.mapCanvas().setExtent(buffered)
        self.iface.mapCanvas().refresh()

    def _highlight_current_feature(self, feature):
        self.iface.mapCanvas().flashFeatureIds(
            self.current_layer, [feature.id()], startColor=QColor(255, 165, 0, 200),
            endColor=QColor(255, 0, 0, 0), flashes=2, duration=500
        )

    def _get_selected_verdict(self):
        checked_id = self.verdict_group.checkedId()
        if checked_id == 1:
            return 1
        elif checked_id == 0:
            return 0
        else:
            return None

    def _save_current(self):
        if not self.features or self.current_index >= len(self.features):
            return False

        verdict = self._get_selected_verdict()
        if verdict is None:
            return True

        feature = self.features[self.current_index]
        fields = self.current_layer.fields()
        field_idx = fields.indexOf(self.review_field)

        if field_idx < 0:
            QMessageBox.warning(
                self, "Error",
                f"Field '{self.review_field}' Data not found data layer.\n"
                "Please create a results field."
            )
            return False

        self.current_layer.startEditing()
        self.current_layer.changeAttributeValue(feature.id(), field_idx, verdict)
        self.current_layer.commitChanges()

        self.features[self.current_index] = next(
            self.current_layer.getFeatures(QgsFeatureRequest().setFilterFid(feature.id()))
        )

        self._update_stats()
        return True

    def _save_and_next(self):
        if not self._save_current():
            return
        if self.current_index < len(self.features) - 1:
            self.current_index += 1
            self._display_current_feature()
        else:
            QMessageBox.information(
                self, "Successful",
                f"The last lot ({len(self.features)} lot).\n"
                "You can go back to previous lot to edit."
            )

    def _go_prev(self):
        self._save_current()
        if self.current_index > 0:
            self.current_index -= 1
            self._display_current_feature()

    def _jump_to(self):
        self._save_current()
        idx = self.jump_spin.value() - 1
        if 0 <= idx < len(self.features):
            self.current_index = idx
            self._display_current_feature()

    def _update_stats(self):
        if not self.features:
            return

        total = len(self.features)
        forest_count = 0
        no_forest_count = 0
        reviewed_count = 0

        fields = self.current_layer.fields()
        field_idx = fields.indexOf(self.review_field)

        if field_idx >= 0:
            for f in self.current_layer.getFeatures():
                val = f.attributes()[field_idx]
                if val == 1:
                    forest_count += 1
                    reviewed_count += 1
                elif val == 0:
                    no_forest_count += 1
                    reviewed_count += 1

        remaining = total - reviewed_count
        pct = int(reviewed_count / total * 100) if total > 0 else 0

        self.progress_bar.setValue(reviewed_count)
        self.progress_bar.setFormat(f"{reviewed_count}/{total} lot ({pct}%)")
        self.reviewed_label.setText(f"Checked: {reviewed_count}")
        self.forest_label.setText(f"Forest: {forest_count}")
        self.no_forest_label.setText(f"Non-forest: {no_forest_count}")
        self.remaining_label.setText(f"Unverified: {remaining}")

    def _save_all(self):
        if not self.current_layer:
            return
        self.current_layer.startEditing()
        self.current_layer.commitChanges()
        QMessageBox.information(
            self, "SAVED",
            "All results have been saved shapefile."
        )

    def _export_csv(self):
        if not self.current_layer or not self.features:
            QMessageBox.warning(self, "Warning", "No data available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save results", "",
            "CSV files (*.csv);;All files (*.*)"
        )
        if not file_path:
            return

        if not file_path.endswith(".csv"):
            file_path += ".csv"

        fields = self.current_layer.fields()
        field_idx = fields.indexOf(self.review_field)
        id_idx = fields.indexOf(self.id_field) if self.id_field else -1

        try:
            import csv
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["STT", "ID_LO", "RESULTS", "DETAIL"])

                for i, feature in enumerate(self.current_layer.getFeatures()):
                    id_val = feature.attributes()[id_idx] if id_idx >= 0 else feature.id()
                    result_val = feature.attributes()[field_idx] if field_idx >= 0 else None

                    if result_val == 1:
                        desc = "forest"
                    elif result_val == 0:
                        desc = "none-forest"
                    else:
                        desc = "Undetermined"

                    writer.writerow([i + 1, id_val, result_val if result_val is not None else "", desc])

            QMessageBox.information(
                self, "Export complet",
                f"The review results have been exported:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Can not export file:\n{str(e)}")

    def _restore_settings(self):
        pass

    def closeEvent(self, event):
        self.settings.sync()
        event.accept()
