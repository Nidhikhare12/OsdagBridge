# osdagbridge/src/report_generator/config/transverse_plotting_core.py
# Data Integration and Extraction Logic for Transverse Members Result Plotting

class TransversePlottingCore:
    def __init__(self, results_data_instance):
        self.results_data = results_data_instance

    def update_member_dropdown(self, dropdown_ui_element):
        """
        Updates the member selection UI dropdown to include Transverse Members
        as a single component as required by specifications.
        """
        dropdown_ui_element.clear()
        dropdown_ui_element.addItem("Longitudinal Members")
        dropdown_ui_element.addItem("Transverse Members (End Diaphragms / Cross Bracings)")

    def extract_transverse_results(self, load_case_id):
        """
        Routes the data extraction through results_data.py and filters OpenSeesPy/ospgrillage
        output dictionary specifically for transverse element tags.
        """
        # Data routing enforced strictly through results_data logic
        raw_results = getattr(self.results_data, "opensees_output_dict", {})
        
        # Matrix to hold all 9 forces and displacements parameters required by task description
        extracted_vectors = {
            "Fx": [], "Fy": [], "Fz": [],
            "Mx": [], "My": [], "Mz": [],
            "dx": [], "dy": [], "dz": []
        }
        
        # Iterating through specific selected load case
        load_case_data = raw_results.get(load_case_id, {})
        for element_tag, data in load_case_data.items():
            # Node/element mapping to accurately distinguish transverse element tags from longitudinal ones
            if self.identify_transverse_tag(element_tag):
                extracted_vectors["Fx"].append(data.get("Fx", 0.0))
                extracted_vectors["Fy"].append(data.get("Fy", 0.0))
                extracted_vectors["Fz"].append(data.get("Fz", 0.0))
                extracted_vectors["Mx"].append(data.get("Mx", 0.0))
                extracted_vectors["My"].append(data.get("My", 0.0))
                extracted_vectors["Mz"].append(data.get("Mz", 0.0))
                extracted_vectors["dx"].append(data.get("dx", 0.0))
                extracted_vectors["dy"].append(data.get("dy", 0.0))
                extracted_vectors["dz"].append(data.get("dz", 0.0))
                
        return extracted_vectors

    def identify_transverse_tag(self, element_tag):
        """
        Analyzes tags retrieved from OpenSeesPy/ospgrillage dictionary to isolate transverse members.
        """
        if isinstance(element_tag, str):
            tag_lower = element_tag.lower()
            # Unified catch for cross bracing chords/diagonals and end diaphragms without separating them
            if "transverse" in tag_lower or "diaphragm" in tag_lower or "bracing" in tag_lower or "dia_" in tag_lower or "cb_" in tag_lower:
                return True
        elif isinstance(element_tag, int):
            # Numerical mapping identifier boundary configuration setup
            if 5000 <= element_tag <= 9000:
                return True
        return False
