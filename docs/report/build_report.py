"""Build docs/report/Substructure_CAD_IFC_Report.pdf (requires reportlab).

Usage (from repo root):  python docs/report/build_report.py
"""
import csv
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
IMG = os.path.join(ROOT, "docs", "images")
OUT = os.path.join(ROOT, "docs", "report", "Substructure_CAD_IFC_Report.pdf")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=10, spaceAfter=6,
                    textColor=colors.HexColor("#1f3b5c"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#1f3b5c"))
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.6, leading=13.2, spaceAfter=5)
BUL = ParagraphStyle("BUL", parent=B, leftIndent=12, bulletIndent=2, spaceAfter=2)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.5, alignment=TA_CENTER,
                     textColor=colors.HexColor("#555555"))
CODE = ParagraphStyle("CODE", parent=ss["Code"], fontSize=7.6, leading=9.4,
                      backColor=colors.HexColor("#f4f4f4"), borderPadding=4)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=20, leading=25,
                       textColor=colors.HexColor("#1f3b5c"))


def P(t, s=B):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(i, BUL, bulletText="•") for i in items]


def fig(name, caption, width=165):
    path = os.path.join(IMG, name)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    img = Image(path, width=width * mm, height=width * mm * h / w)
    return KeepTogether([img, P(caption, CAP), Spacer(1, 4)])


def table(rows, widths, header=True, font=8.3):
    t = Table([[Paragraph(str(c), ParagraphStyle("c", parent=B, fontSize=font, leading=font + 2,
                                                  spaceAfter=0)) for c in r] for r in rows],
              colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b0b0")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe5f1"))]
    t.setStyle(TableStyle(style))
    return t


def checks_rows():
    path = os.path.join(ROOT, "samples", "detailing_checks_default.csv")
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    out = [["", "Member", "Check", "Reference", "Required", "Provided"]]
    for r in rows:
        out.append([r["status"], r["component"], r["check"], r["reference"], r["required"], r["provided"]])
    return out


def boq_rows():
    path = os.path.join(ROOT, "samples", "boq_skew0.csv")
    with open(path) as fh:
        return list(csv.reader(fh))


def build():
    story = []
    story += [Spacer(1, 30),
              P("Parametric 3D CAD Modelling of Bridge Substructure and IFC Workflow Integration", TITLE),
              Spacer(1, 6),
              P("OsdagBridge screening task — report", ParagraphStyle("st", parent=B, fontSize=12,
                                                                     alignment=TA_CENTER)),
              Spacer(1, 4),
              P("Submitted by: <b>Aditya Sarna</b>", ParagraphStyle("au", parent=B, fontSize=11,
                                                                    alignment=TA_CENTER)),
              Spacer(1, 14),
              fig("ifc_reimport_skew10.png",
                  "Exported IFC4 file re-opened through IfcOpenShell: plate-girder superstructure and the "
                  "new hammerhead substructure (10° skew), with the reinforcement visible inside the concrete.", 160),
              Spacer(1, 6),
              table([["Item", "Result"],
                     ["Components modelled", "Hammerhead pier cap (tapered cantilevers; trapezoidal option), "
                      "circular pier, bearing pedestals, pile cap, 2×2 bored piles; bent and anchored "
                      "reinforcement in every concrete member"],
                     ["Engineering checks", "20 detailing checks (IS 456, IRC 112, IS 2911, IRC 78) run on every "
                      "model and shown in the Log dock; the warnings trace back to task-prescribed values"],
                     ["Integration", "builder.py per component → cad_generator.py → cad_3d.py (semi-transparent "
                      "concrete, opaque rebar) → IFC exporter"],
                     ["IFC output", "IFC4: 24 concrete elements and 948 IfcReinforcingBar (straight bridge) "
                      "together with the superstructure; 0 schema errors and 0 EXPRESS-rule errors"],
                     ["BOQ from IFC", "47.05 m³ substructure concrete, 2,990 kg reinforcement (straight bridge)"],
                     ["Tests", "21 new pytest cases pass; the repository's 5 existing tests still pass"],
                     ["Video demonstration", '<link href="https://youtu.be/h6h36OT0hyM" color="blue">'
                      'https://youtu.be/h6h36OT0hyM</link>']],
                    [38, 132]),
              PageBreak()]

    # ------------------------------------------------------------------ 1
    story += [P("1. Introduction and scope", H1),
              P("OsdagBridge already modelled the plate-girder superstructure (girders, stiffeners, cross "
                "bracing, deck, crash barriers, railings) and exported it to IFC. The substructure folders "
                "(<i>sub_structure/pier, pier_cap, pedestal</i> and <i>foundation/pile, pile_cap</i>) held only "
                "empty placeholders. This work adds parametric pythonOCC models of the whole substructure with "
                "reinforcement, displays them in the CAD window, and passes them through the IFC exporter so "
                "that the .ifc file contains the complete bridge."),
              P("Default dimensions (mm) are the ones given in the task and are hard-coded as module constants "
                "in each <i>builder.py</i>:"),
              table([["Component", "Parameter", "Default"],
                     ["Pier", "pier_diameter / pier_height", "800 / 3000"],
                     ["Pier cap", "top width / bottom width / depth / length", "3000 / 1200 / 600 / = deck width"],
                     ["Pile cap", "length (Y) / width (X) / depth", "2200 / 1200 / 600"],
                     ["Piles", "number / diameter / length / spacing", "4 (2×2) / 400 / 5000 / 600 c/c"],
                     ["Reinforcement", "main Ø @ spacing / ties Ø @ spacing / cover",
                      "16 @ 150 / 8 @ 200 / 40"],
                     ["Pedestal (added)", "length × width × height, bearing gap", "600 × 600 × 150, 100"]],
                    [32, 80, 58])]

    # ------------------------------------------------------------------ 2
    story += [P("2. Methodology", H1),
              P("2.1 Studying the existing architecture", H2),
              P("The plate-girder pipeline was traced end to end before writing any geometry:"),
              *bullets([
                  "<b>Component builders</b> (<i>core/bridge_components/super_structure/*/builder.py</i>) return "
                  "OCC shapes built in a local frame.",
                  "<b>cad_generator.py</b> (<i>core/bridge_types/plate_girder</i>) receives a "
                  "<i>BridgeParametersDTO</i>, calls each builder, places the shapes (girder offsets, skew "
                  "shift <i>x = y·tan θ</i>) and returns a <i>model_data</i> dictionary.",
                  "<b>cad_3d.py</b> (<i>desktop/ui</i>) displays each <i>model_data</i> key with "
                  "<i>display_and_register()</i> and drives the visibility checkboxes.",
                  "<b>IFC export</b>: <i>template_page.save3DcadImages()</i> → <i>PlateGirderIfcExportHandler</i> "
                  "→ <i>PlateGirderIFCExtractor</i> (re-derives parametric objects from the DTO) → "
                  "<i>BridgeIfcGenerator</i> (writes IFC4 entities with IfcOpenShell).",
              ]),
              P("Reading the girder builder gave the coordinate system actually used: X runs from 0 to L along "
                "the span, the deck is centred on Y = 0, and Z = 0 is at girder mid-depth; the bearings sit at "
                "X = 0 and X = L under the bottom-flange soffit (Z = −D/2 − t<sub>fb</sub>). The task suggests an "
                "origin at mid-span, deck level, but the substructure was deliberately built in the "
                "<b>existing</b> frame so that it lines up with the superstructure without moving any existing "
                "geometry (see Challenges)."),

              P("2.2 Two-layer design: layout data + OCC solids", H2),
              P("Every substructure builder exposes two functions:"),
              *bullets([
                  "<b>*_layout()</b> – pure Python, no OCC. Returns dimensions, the concrete description "
                  "(cylinder / box / lofted trapezoidal sections), the volume, and a list of <i>bar records</i> (role "
                  "MAIN/LIGATURE, diameter, centre-line polyline, length, host).",
                  "<b>build_*()</b> – converts a layout into OCC solids (BRepPrimAPI cylinders, boxes, prisms; "
                  "rebar as cylinders and tori).",
              ]),
              P("The CAD generator and the IFC exporter both consume the same layout, so the IFC geometry, the "
                "quantities and the on-screen model cannot drift apart. The layout layer is also easy to unit-test "
                "(cover, counts, spacing) without a display."),

              P("2.3 Geometry of each component", H2),
              table([["Component (file)", "Geometry and engineering logic"],
                     ["Pier cap<br/><i>sub_structure/pier_cap/builder.py</i>",
                      "<b>Hammerhead.</b> Longitudinal section: trapezoid 3000 top / 1200 soffit. Transverse "
                      "elevation: full 600 mm depth over the pier zone (pier group + 300 mm haunch offset each "
                      "side), cantilevers tapering linearly to 0.5 × depth at the tips. Built as a ruled loft "
                      "(BRepOffsetAPI_ThruSections) through trapezoidal sections at the taper stations; every face "
                      "is planar, so the solid is exact and its volume (Simpson's rule, exact for the quadratic "
                      "section area) equals the OCC mass property to 1e-6. <i>pier_cap_style='TRAPEZOIDAL'</i> "
                      "gives a constant-depth prism. Length defaults to the deck width (÷ cos θ when skewed)."],
                     ["Pier<br/><i>sub_structure/pier/builder.py</i>",
                      "Vertical BRepPrimAPI_MakeCylinder, top touching the pier-cap soffit."],
                     ["Pedestal<br/><i>sub_structure/pedestal/builder.py</i>",
                      "Box under each girder line on the cap top; pedestal height + 100 mm bearing gap fill the "
                      "space up to the girder soffit, where the existing support glyphs are drawn. Reinforced with "
                      "top and bottom Ø8 @ 100 bursting meshes and four Ø16 corner dowels into the cap."],
                     ["Pile cap<br/><i>foundation/pile_cap/builder.py</i>",
                      "BRepPrimAPI_MakeBox, 1200 (X) × 2200 (Y) × 600, centred on the pier."],
                     ["Piles<br/><i>foundation/pile/builder.py</i>",
                      "n<sub>x</sub> × n<sub>y</sub> grid (default 2 × 2 at 600 c/c; optional separate Y spacing) "
                      "of cylinders; the heads project 50 mm into the cap (IS 2911), and that volume is subtracted "
                      "from the cap's net volume so the BOQ does not double-count."],
                     ["Assembly<br/><i>sub_structure/substructure_builder.py</i>",
                      "<i>SubstructureParams</i> dataclass; stacks pedestal → cap → pier → pile cap → piles at "
                      "X = 0 and X = L; supports several piers per support line; builds one rigid transform per "
                      "support (rotation −θ about Z, then translation)."]],
                    [48, 122]),
              Spacer(1, 4),
              P("2.4 Reinforcement detailing", H2),
              P("Bars are placed from the concrete faces using clear cover c = 40 mm, tie diameter d<sub>t</sub> "
                "and main diameter d<sub>m</sub>:"),
              *bullets([
                  "<b>Circular members (pier, piles)</b>: cage radius r = R − c − d<sub>t</sub> − d<sub>m</sub>/2; "
                  "number of bars n = max(6, ⌈2πr / 150⌉) (IS 456 cl. 26.5.3.1 minimum of six) → 15 bars in the "
                  "pier, 7 in each pile. Ties are rings of centre-line radius R − c − d<sub>t</sub>/2 at 200 c/c.",
                  "<b>Starter bars</b>: pier bars are L-bars – they rest on the pile-cap bottom mat with a 12d "
                  "foot turned outwards, and end under the pier-cap top steel with a 12d leg turned inwards. "
                  "Pile bars run up into the cap with an inward 12d bend (inward so the hook keeps cover at "
                  "close pile spacing). Leg lengths are clipped automatically when the geometry is tight.",
                  "<b>Pier cap</b>: at every stirrup position the local section (top 3000, depth from the "
                  "hammerhead soffit) is offset inwards by c + d<sub>t</sub>/2 (convex-polygon offset by "
                  "intersecting offset edges), so stirrups shorten along the cantilever. Top bars run straight "
                  "and are bent down at both tips; bottom bars follow the tapered soffit (cranked at the taper "
                  "stations) and are bent up at the tips.",
                  "<b>Pile cap</b>: bottom mat of Ø16 <b>U-bars</b> at ≤ 150 both ways, resting on the pile heads, "
                  "with both legs bent up the side faces to just below the top mat (full anchorage beyond the "
                  "outer piles); top mat Ø8 at ≤ 200 both ways.",
                  "<b>Development length</b> is computed per IS 456 cl. 26.2.1 (L<sub>d</sub> = 0.87 f<sub>y</sub> φ "
                  "/ 4τ<sub>bd</sub>, τ<sub>bd</sub> from the concrete grade × 1.6 for deformed bars), crediting "
                  "a 90° bend with 8φ (cl. 26.2.2.1).",
                  "<b>Closed ties and stirrups</b> are modelled as open polylines that go round once and "
                  "overlap by a lap of max(10d, 75 mm). This matches how the bar is bent, includes the lap in BOQ "
                  "lengths, and is needed for valid IFC swept-disk solids (Section 3.4).",
              ]),
              P("2.5 Detailing checks", H2),
              P("<i>sub_structure/pier/checks.py</i> and <i>foundation/pile/checks.py</i> (previously empty) "
                "check the modelled reinforcement against the detailing rules of IS 456, IRC 112, IS 2911 and "
                "IRC 78. <i>run_detailing_checks()</i> runs on every CAD generation and the result goes to the "
                "application's Log dock and to the hover labels. They are detailing checks, not a strength "
                "design. Results for the task defaults:"),
              table(checks_rows(), [12, 15, 43, 46, 22, 32], font=6.9),
              P("All warnings come from values fixed by the task: pile spacing 600 mm (1.5 D), 40 mm cover on "
                "piles in soil, and a 1200 mm pile-cap width that leaves 100 mm beyond the outer pile face. The "
                "anchorage of the pier starters (638 vs 640 mm) is a knock-on effect of the 600 mm cap depth; "
                "the check is kept conservative (bend credited at 8φ only). A test sets pile_spacing = 1200, a "
                "1900 × 1900 × 650 cap and 50 mm cover, and confirms all checks then pass.", B),
              P("2.6 Routing through the workflow", H2),
              *bullets([
                  "<b>dto.py</b>: new optional fields <i>include_substructure</i> and <i>substructure_params</i> "
                  "(defaults to the hard-coded builder values).",
                  "<b>cad_generator.py</b>: <i>_set_parameters()</i> reads them; a new step 12 "
                  "(<i>_build_substructure</i>) computes the girder soffit (including segmented girders) and the "
                  "girder Y positions and calls <i>build_substructure()</i>. New <i>model_data</i> keys: "
                  "pier_caps, pedestals, piers, pile_caps, piles, substructure_rebars, substructure_layout, "
                  "substructure_checks. "
                  "<i>create3Dcad()</i> therefore also puts the substructure into STEP/IGES/STL/BREP exports.",
                  "<b>cad_3d.py</b>: concrete is drawn with <i>transparency = 0.65</i> (opacity 0.35) and the "
                  "rebar compound in an opaque steel colour; new <b>Substructure</b> and <b>Reinforcement</b> "
                  "checkboxes and hover labels with the dimensions and the detailing-check summary.",
                  "<b>bridge_cad_extraction.py</b>: the IFC girder layout now uses the designed number of girders "
                  "and spacing from the DTO (it used to re-derive 6 girders where the design had 5), so the IFC "
                  "superstructure and the pedestals under it match the CAD model.",
                  "<b>input_dock.py</b>: guarded an existing call to a missing "
                  "<i>notify_additional_inputs_footpath</i> hook that raised an AttributeError whenever the "
                  "Footpath option was changed.",
              ]),
              fig("support_closeup_right.png",
                  "Figure 1 – Elevation along the support line: hammerhead pier cap (soffit tapering to the tips, "
                  "stirrups shortening with it), reinforced pedestals, pier with ties and L-bar starters, pile cap "
                  "U-bars and pile cages (semi-transparent concrete).", 150),
              fig("closeup_short_cap_iso.png",
                  "Figure 2 – Close-up of one support (pier cap shortened to 3.6 m through the parameter "
                  "pier_cap_length so the bars can be read): concrete at opacity 0.35, opaque rebar.", 120),
              fig("closeup_rebar_cage.png", "Figure 3 – The reinforcement cage alone: bent pier-cap bars following "
                  "the soffit, L-bar starters, pile-cap U-bars, pile cages.", 120),
              fig("full_bridge_iso.png", "Figure 4 – Full bridge: superstructure on the two substructure "
                  "supports.", 150)]

    # ------------------------------------------------------------------ 3
    story += [P("3. IFC integration", H1),
              P("3.1 Data path", H2),
              P("<i>File → Save 3D Model → IFC</i> calls <i>backend.get_ifc_export_parameters()</i> (a "
                "BridgeParametersDTO) and <i>PlateGirderIfcExportHandler.export()</i>. Two hooks were added:"),
              *bullets([
                  "<b>PlateGirderIFCExtractor._extract_substructure()</b> (bridge_cad_extraction.py) – calls the "
                  "same <i>substructure_layout()</i> with the extractor's deck width, girder layout and skew, and "
                  "adds the result as <i>extracted_dict['substructure']</i>.",
                  "<b>BridgeIfcGenerator.generate_from_extracted_data()</b> – after the superstructure, passes "
                  "that list to the new <b>SubstructureIfcWriter</b> (core/ifc_export_bridge/substructure_ifc.py).",
              ]),
              P("3.2 Spatial structure, global axis and relative local axes", H2),
              Preformatted(
                  "IfcProject  (units: m, m2, m3, rad, kg)\n"
                  " +- IfcSite 'Default Site'\n"
                  "    +- IfcBuilding 'Bridge Structure'\n"
                  "       +- IfcBuildingStorey 'Superstructure'  (existing)\n"
                  "       +- IfcBuildingStorey 'Substructure'    pier caps, pedestals, piers + their bars\n"
                  "       +- IfcBuildingStorey 'Foundation'      pile caps, piles + their bars\n\n"
                  "IfcLocalPlacement chain\n"
                  "  storey placement        global origin, global X/Y/Z\n"
                  "   +- support placement    origin = support point, RefDirection = (cos(-skew), sin(-skew), 0)\n"
                  "      +- element placement origin of the element in the support frame\n"
                  "         +- rebar placement relative to its host element", CODE),
              Spacer(1, 4),
              P("The project keeps one global axis (that of the existing export) and every element gets its "
                "own local axes nested under it, so a BIM tool can move a whole support by editing a single "
                "placement, and the coordinates inside elements stay small."),
              P("3.3 Entity mapping", H2),
              table([["Member", "IFC4 entity / type", "Geometry", "Quantity set"],
                     ["Pier", "IfcColumn, ObjectType 'Pier', COLUMN", "IfcCircleProfileDef + IfcExtrudedAreaSolid",
                      "Qto_ColumnBaseQuantities"],
                     ["Pier cap", "IfcBeam, USERDEFINED / 'PierCap'",
                      "IfcFacetedBrep (exact planar-faced loft of the hammerhead)", "Qto_BeamBaseQuantities"],
                     ["Pedestal", "IfcBuildingElementProxy / 'Pedestal'", "IfcRectangleProfileDef extrusion",
                      "Qto_BuildingElementProxyQuantities"],
                     ["Pile cap", "IfcFooting, PILE_CAP", "IfcRectangleProfileDef extrusion",
                      "Qto_FootingBaseQuantities (Gross; Net = gross − pile heads)"],
                     ["Pile", "IfcPile, BORED, CAST_IN_PLACE", "IfcCircleProfileDef extrusion",
                      "Qto_PileBaseQuantities"],
                     ["Rebar", "IfcReinforcingBar MAIN / LIGATURE + IfcReinforcingBarType per Ø and role",
                      "IfcSweptDiskSolid on a 3D IfcPolyline", "Qto_ReinforcingElementBaseQuantities"]],
                    [20, 52, 55, 43]),
              Spacer(1, 4),
              P("IfcOpenShell functions and entities used: <i>ifcopenshell.file.create_entity / createIfc*</i>, "
                "IfcLocalPlacement, IfcAxis2Placement3D, IfcShapeRepresentation ('SweptSolid', 'Brep', "
                "'AdvancedSweptSolid'), IfcFacetedBrep / IfcClosedShell / IfcPolyLoop, IfcProductDefinitionShape, IfcStyledItem / IfcSurfaceStyle / "
                "IfcSurfaceStyleRendering (concrete transparency 0.65, as in the GUI), IfcMaterial + "
                "IfcRelAssociatesMaterial ('Concrete M35', 'Reinforcement Steel Fe 500'), IfcElementQuantity + "
                "IfcQuantityLength/Area/Volume/Weight/Count, IfcPropertySet via the existing "
                "<i>BridgeMetadataMapper.assign_metadata()</i> (Pset_ConcreteElementGeneral, "
                "Pset_OsdagSubstructure, Pset_OsdagReinforcement), IfcRelContainedInSpatialStructure (one per "
                "storey), IfcRelAggregates (building → new storeys), IfcRelDefinesByType and IfcRelDeclares "
                "(rebar types declared in the project). A KILOGRAM mass unit was added for rebar weights."),
              P("3.4 Validation and BOQ", H2),
              *bullets([
                  "<b>ifcopenshell.validate</b> with EXPRESS rules enabled reports 0 issues. Two existing problems "
                  "were fixed along the way: IfcSurfaceStyleRendering lacked the mandatory ReflectanceMethod, and "
                  "IfcOwnerHistory had ChangeAction without LastModifiedDate (rule WR1).",
                  "<b>Geometry</b>: every substructure element and every one of the 948 bars (bent bars included) "
                  "tessellates with ifcopenshell.geom; mesh volumes match the exported GrossVolume quantities "
                  "within 1 % (the hammerhead brep exactly).",
                  "<b>BOQ</b>: <i>scripts/substructure/ifc_boq.py</i> reads only the IFC quantities back and produces the table "
                  "below — the same data a Revit schedule (Structural Columns / Foundations / Rebar: Volume, "
                  "Length, Weight, Count) would use. IfcColumn, IfcFooting, IfcPile and IfcReinforcingBar map to "
                  "native Revit categories on import.",
                  "<b>Revit</b>: the file uses only IFC4 constructs that Revit's IFC importer supports "
                  "(extrusions, faceted breps, swept-disk rebar, Qto base quantities, materials, types). It was "
                  "validated with IfcOpenShell; it has not been opened in Revit itself in this environment "
                  "(no Windows/Revit available).",
              ]),
              table(boq_rows(), [24, 72, 26, 12, 12, 22], font=7.6),
              P("Table – BOQ produced from samples/osdagbridge_super_sub_skew0.ifc (two supports).", CAP),
              fig("ifc_reimport_substructure.png",
                  "Figure 5 – Substructure storeys of the IFC file re-tessellated by IfcOpenShell.", 150)]

    # ------------------------------------------------------------------ 4
    story += [P("4. Challenges", H1),
              *bullets([
                  "<b>Coordinate system.</b> The task describes an origin at mid-span, deck level; the existing "
                  "superstructure uses X = 0…L and Z = 0 at girder mid-depth. Moving the superstructure would "
                  "have touched every existing builder and the 2D drawings, so the substructure was built in the "
                  "existing frame and the support frames are defined relative to it. Changing the global origin "
                  "later only needs one offset per support.",
                  "<b>Skew sign convention.</b> <i>cad_generator</i> negates the DTO skew angle while the IFC "
                  "extractor receives the DTO directly; the substructure takes the already-normalised angle from "
                  "each side so pier caps stay parallel to the skewed girder ends in both outputs.",
                  "<b>Two different girder layouts.</b> The existing IFC extractor re-solved the number of girders "
                  "from the deck width (6 girders for the test bridge, where the design had 5), so IFC pedestals "
                  "did not line up with the CAD. The extractor now uses the designed girder count and spacing.",
                  "<b>Hammerhead geometry.</b> A boolean intersection of two prisms would work in OCC but becomes "
                  "an IfcBooleanResult in IFC, which importers handle unevenly. Describing the cap as a ruled loft "
                  "through trapezoidal sections keeps every face planar, so the same station data gives an exact "
                  "OCC solid and an exact IfcFacetedBrep.",
                  "<b>Closed rebar loops in IFC.</b> IfcSweptDiskSolid along a closed polyline (and "
                  "IfcSweptDiskSolidPolygonal with fillets on a closed loop) failed to tessellate in IfcOpenShell. "
                  "Modelling ties as open polylines with a 10d lap fixed every bar and is closer to real detailing.",
                  "<b>Environment.</b> ifcopenshell was not in environment.yml (added). On macOS 26 the conda "
                  "environment has both pip-PySide6 and conda Qt; Qt only started with QT_PLUGIN_PATH pointing to "
                  "PySide6's plugins, and an offscreen OCC viewer segfaulted while creating the OpenGL context. "
                  "Model images were therefore rendered with the stock pythonOCC Qt viewer "
                  "(scripts/substructure/render_substructure.py) using the same colours and transparency as cad_3d.py.",
                  "<b>Performance.</b> About 950 bars (several thousand OCC solids, counting bar legs) are built "
                  "per model. Solids are built once in the support frame, packed into compounds and moved with a "
                  "single TopLoc_Location per support; the full bridge with substructure generates in ~0.6 s and "
                  "the IFC export takes ~0.5 s.",
                  "<b>Task values versus codes.</b> Some prescribed values (600 mm pile spacing, 40 mm cover on "
                  "piles, 1200 mm pile-cap width) fall outside IS 2911 / IRC 78 detailing rules. They were kept "
                  "as defaults because the task prescribes them, and the detailing checks flag each one with the "
                  "value that would satisfy the code.",
              ])]

    # ------------------------------------------------------------------ 5
    story += [P("5. Testing", H1),
              P("<i>tests/integration/test_substructure.py</i> (21 tests, all passing) checks: default "
                "dimensions; vertical stacking and the bearing gap; pier-cap length versus deck width and skew; "
                "the 2×2 pile grid; clear cover for every bar in every member; at least six bars and 200 mm tie "
                "pitch in circular members; ties as lapped open polylines; quantity summary; CAD keys and "
                "<i>create3Dcad</i> with skew; switching the substructure off; IFC content per storey; schema and "
                "EXPRESS-rule validity; relative placement chain, materials, types and quantities; tessellation "
                "of every element and bar, with volumes matching quantities; hammerhead taper and core; OCC "
                "volume = analytic volume for both cap styles; bent / U / L bars and pedestal steel; IS 456 "
                "development length; detailing checks flag the task defaults and all pass for code-compliant "
                "inputs; IFC girders and pedestals match the design. The repository's existing tests still pass."),
              P("6. File structure", H1),
              Preformatted(
                  "src/osdagbridge/core/bridge_components/\n"
                  "  sub_structure/\n"
                  "    substructure_builder.py      SubstructureParams, layout, OCC assembly, BOQ helper\n"
                  "    reinforcement/builder.py     RebarParams, bar layouts, OCC bar solids\n"
                  "    pier/builder.py, checks.py   circular pier + cage; pier & pier-cap detailing checks\n"
                  "    pier_cap/builder.py          hammerhead cap + stirrups / longitudinal bars\n"
                  "    pedestal/builder.py          bearing pedestals\n"
                  "  foundation/\n"
                  "    pile_cap/builder.py          pile cap + mats\n"
                  "    pile/builder.py, checks.py   pile grid + cages; pile & pile-cap detailing checks\n"
                  "src/osdagbridge/core/bridge_types/plate_girder/{dto.py, cad_generator.py}   (modified)\n"
                  "src/osdagbridge/desktop/ui/cad_3d.py                                    (modified)\n"
                  "src/osdagbridge/core/ifc_export_bridge/\n"
                  "    substructure_ifc.py          new IFC writer\n"
                  "    bridge_cad_extraction.py, bridge_ifc_generator.py, bridge_geometry_mapper.py (modified)\n"
                  "tests/integration/{test_substructure.py, sample_params.py}\n"
                  "scripts/substructure/{render_substructure.py, render_ifc.py, ifc_boq.py, detailing_checks.py}\n"
                  "samples/  example .ifc files (0° and 10° skew), BOQ csv, detailing-check csv\n"
                  "SUBSTRUCTURE_README.md", CODE),
              P("Video demonstration", H2),
              P('A silent screen recording of the GUI workflow (design, 3D CAD with semi-transparent concrete '
                'and visible reinforcement, Substructure / Reinforcement toggles, and IFC export) is available '
                'at <link href="https://youtu.be/h6h36OT0hyM" color="blue">https://youtu.be/h6h36OT0hyM</link> '
                '(also included in the submission ZIP).'),
              P("7. References", H1),
              *bullets([
                  "pythonOCC-core documentation and examples – https://github.com/tpaviot/pythonocc-core, "
                  "https://dev.opencascade.org/doc/overview/html/ (BRepPrimAPI, BRepBuilderAPI, gp_Trsf, "
                  "TopLoc_Location, AIS transparency).",
                  "IfcOpenShell documentation – https://docs.ifcopenshell.org/ (ifcopenshell.file, geom, validate, "
                  "util.element, util.shape).",
                  "buildingSMART IFC4 ADD2 TC1 specification – https://standards.buildingsmart.org/IFC/RELEASE/"
                  "IFC4/ADD2_TC1/HTML/ (IfcReinforcingBar, IfcSweptDiskSolid, IfcPile, IfcFooting, Qto_* base "
                  "quantity sets, IfcLocalPlacement).",
                  "IS 456:2000 Plain and Reinforced Concrete – Code of Practice (cover, minimum bars in circular "
                  "columns, ties).",
                  "IS 2911 (Part 1/Sec 2):2010 Design and Construction of Pile Foundations – bored cast-in-situ piles.",
                  "IRC 112:2020 Code of Practice for Concrete Road Bridges; IRC 78:2014 Foundations and Substructure.",
                  "IS 13920:2016 Ductile Design and Detailing – hook / lap length for closed ties.",
                  "OsdagBridge repository and existing builders – https://github.com/Nidhikhare12/OsdagBridge (dev).",
              ])]

    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title="Substructure 3D CAD and IFC Integration – OsdagBridge",
                            author="Aditya Sarna")

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {d.page}")
        canvas.drawString(18 * mm, 9 * mm, "Aditya Sarna – OsdagBridge Substructure CAD & IFC integration")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
