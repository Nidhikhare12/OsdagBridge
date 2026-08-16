import copy
from osdag.component.tension_bolted import Tension_bolted
from osdag.component.tension_welded import Tension_welded
from osdag.component.compression_bolted import Compression_bolted
from osdag.component.compression_welded import Compression_welded
from osdag.component.rolled_section import RolledSectionDesign  # अगर नाम अलग हो तो प्रोजेक्ट के अनुसार बदलें
from osdag.component.welded_girder import WeldedGirderDesign
def design_end_diaphragm(connection_type, design_dict_struts, design_dict_tens, analysis_results=None, element_ids=None, load_case=None):
    """
    यह फ़ंक्शन एंड डायाफ्राम के सभी ऑप्शंस (Bracing, Rolled, Welded) 
    और ऑटोमेटेड फ़ोर्स मैपिंग को हैंडल करता है।
    """
    # 1. यदि यूज़र ने Rolled Section या Welded Plate Girder चुना है
    if connection_type in ["Rolled Section", "Welded Plate Girder"]:
        # एनालिसिस रिज़ल्ट्स से Shear (V) और Moment (M) ऑटोमैटिकली रीड करना
        if analysis_results and element_ids and load_case:
            shear_v, moment_m = analysis_results.get_transverse_member_forces(element_ids, load_case)
            
        design_dict_struts['Load']['Shear Force (kN)'] = shear_v
        design_dict_struts['Load']['Bending Moment (kNm)'] = moment_m
        # Osdag के मॉड्यूल को कॉल करना
        if connection_type == "Rolled Section":
            # यहाँ रोल्ड सेक्शन डिज़ाइन का फ़ंक्शन आएगा
         rolled_output = RolledSectionDesign(design_dict_struct).get_output_dictionary()
        return rolled_output
    elif connection_type == "Welded Plate Girder":
            # यहाँ वेल्डेड गर्डर डिज़ाइन का फ़ंक्शन आएगा
        welded_output = WeldedGirderDesign(design_dict_struct).get_output_dictionary()
        return welded_output
            

    # 2. यदि यूज़र ने Cross Bracing (Welded/Bolted) चुना है (पुराना लॉजिक)
    if connection_type == "Welded" or connection_type == "Cross Bracing (Welded)":
        design_dict_struts['Connection']['Type'] = 'Welded'
        design_dict_tens['Connection']['Type'] = 'Welded'
        
        strut_output = Compression_welded(design_dict_struts).get_output_dictionary()
        tension_output = Tension_welded(design_dict_tens).get_output_dictionary()
    else:
        # Bolted विकल्प के लिए
        strut_output = Compression_bolted(design_dict_struts).get_output_dictionary()
        tension_output = Tension_bolted(design_dict_tens).get_output_dictionary()
        return design_dict_struts, {}
    return strut_output, tension_output