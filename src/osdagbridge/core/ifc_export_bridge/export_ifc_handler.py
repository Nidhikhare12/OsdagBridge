"""
Export Handler for Plate Girder IFC
Connects the UI export button directly to the ifc_export_bridge engine.
Runs as an isolated background task.
"""
import sys
import threading
from osdagbridge.core.ifc_export_bridge.bridge_cad_extraction import PlateGirderIFCExtractor
from osdagbridge.core.ifc_export_bridge.bridge_ifc_generator import BridgeIfcGenerator

class PlateGirderIfcExportHandler:
    """Handles the extraction and generation lifecycle of the IFC file without blocking GUI."""

    def __init__(self, cad_generator, filepath, completion_callback=None):
        self.cad_generator = cad_generator
        self.filepath = filepath
        self.callback = completion_callback

    def _get_substructure_parts(self):
        """Substructure Parts built by PlateGirderCADGenerator.generate().

        They live in model_data so the IFC uses exactly the same geometry as the 3D view.
        Returns None if the substructure was not generated (IFC then has superstructure only).
        """
        model_data = getattr(self.cad_generator, "model_data", None) or {}
        return model_data.get("substructure_parts")

    def export(self):
        """Extracts and Maps synchronously."""
        try:
            extractor = PlateGirderIFCExtractor(self.cad_generator)
            extracted_dict = extractor.extract()

            generator = BridgeIfcGenerator(self.filepath)
            generator.generate_from_extracted_data(
                extracted_dict,
                self.cad_generator,
                substructure_parts=self._get_substructure_parts(),
            )

            if self.callback:
                self.callback(True, f"Model successfully exported to {self.filepath}")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(error_msg)
            if self.callback:
                self.callback(False, str(e))

    def export_async(self):
        """Triggers export in a background thread to keep the Qt UI responsive."""
        thread = threading.Thread(target=self.export)
        thread.daemon = True
        thread.start()