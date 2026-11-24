"""Write vml-corpus.docx: one VML case per page, labelled ``[case <id>]``, for comparing renderers against Word.

The cases cover the VML elements and attributes Word writes (ECMA-376 Part 4, §19 VML; MS-OI29500): primitives,
every path command, all legacy preset shape types (shapetypes.json, written by Word), stroke, fill, transforms,
groups, text boxes and their text direction, shadow, text paths, pictures, floating placement and connectors.
Usage: make_corpus.py OUT.docx [shapetypes.json]
"""
import io
import json
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
SHAPETYPES = {int(k): v for k, v in json.loads((Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'shapetypes.json').read_text()).items()}

# Two shapetypes Word writes for connectors (not among the autoshape presets).
SHAPETYPES[32] = ('<v:shapetype id="_x0000_t32" coordsize="21600,21600" o:spt="32" o:oned="t" path="m,l21600,21600e" '
                  'filled="f"><v:path arrowok="t" fillok="f" o:connecttype="none"/><o:lock v:ext="edit" '
                  'shapetype="t"/></v:shapetype>')
SHAPETYPES[34] = ('<v:shapetype id="_x0000_t34" coordsize="21600,21600" o:spt="34" o:oned="t" adj="10800" '
                  'path="m,l@0,0@0,21600,21600,21600e" filled="f"><v:stroke joinstyle="miter"/><v:formulas>'
                  '<v:f eqn="val #0"/></v:formulas><v:path arrowok="t" fillok="f" o:connecttype="none"/>'
                  '<v:handles><v:h position="#0,center"/></v:handles><o:lock v:ext="edit" shapetype="t"/></v:shapetype>')

FILL, STROKE = '#9fc5e8', '#1f3864'
cases: list[tuple[str, str, str]] = []      # (id, description, paragraph XML after the label)
_defined: set[int] = set()


def typedef(spt: int) -> str:
    """The shapetype the first time a case uses it, as Word writes it once per document."""
    if spt in _defined:
        return ''
    _defined.add(spt)
    return SHAPETYPES[spt]


def typed(spt: int, pict_xml: str) -> str:
    """*pict_xml* (a ``w:pict``) with the shapetype it uses written first, the first time."""
    return '<w:pict>' + typedef(spt) + pict_xml[len('<w:pict>'):]


def para(inner: str, ppr: str = '') -> str:
    return f'<w:p>{ppr}<w:r>{inner}</w:r></w:p>'


def pict(inner: str) -> str:
    return f'<w:pict>{inner}</w:pict>'


def case(cid: str, desc: str, body: str) -> None:
    cases.append((cid, desc, body))


def shape(attrs: str = '', inner: str = '', tag: str = 'v:rect', size: str = 'width:144pt;height:72pt', style: str = '') -> str:
    colors = ('' if 'fillcolor=' in attrs else f'fillcolor="{FILL}" ') + f'strokecolor="{STROKE}" strokeweight="1.5pt"'
    return pict(f'<{tag} style="{size}{";" + style if style else ""}" {colors} {attrs}>{inner}</{tag}>')


# --- primitives -------------------------------------------------------------------------------------------------
case('prim-rect', 'v:rect', para(shape()))
case('prim-roundrect', 'v:roundrect arcsize=30%', para(shape('arcsize="0.3"', tag='v:roundrect')))
case('prim-oval', 'v:oval', para(shape(tag='v:oval')))
case('prim-oval-typed', 'v:oval with type="#_x0000_t3" (as .doc writes it)', para(pict(
    '<v:shapetype id="_x0000_t3" coordsize="21600,21600" o:spt="3" path="al10800,10800,10800,10800,0,23592960xe"/>'
    f'<v:oval type="#_x0000_t3" style="width:144pt;height:72pt" fillcolor="{FILL}" strokecolor="{STROKE}" strokeweight="1.5pt"/>')))
case('prim-line', 'v:line from/to', para(pict(f'<v:line from="0,0" to="144pt,72pt" strokecolor="{STROKE}" strokeweight="2pt"/>')))
case('prim-polyline', 'v:polyline points', para(pict(
    f'<v:polyline points="0,72pt,36pt,0,72pt,60pt,108pt,10pt,144pt,72pt" filled="f" strokecolor="{STROKE}" strokeweight="2pt"/>')))
case('prim-curve', 'v:curve from/control1/control2/to', para(pict(
    f'<v:curve from="0,72pt" control1="36pt,-40pt" control2="108pt,110pt" to="144pt,0" filled="f" strokecolor="{STROKE}" strokeweight="2pt"/>')))
case('prim-arc', 'v:arc startangle=0 endangle=270', para(shape('startangle="0" endangle="270" filled="f"', tag='v:arc')))

# --- path commands (coordsize 100,100) ---------------------------------------------------------------------------
PATHS = {
    'm-l-x-e': 'm10,10l90,10,90,90,10,90xe',
    'r-relative-line': 'm10,10r80,0,0,80,-80,0xe',
    'c-curve': 'm5,50c30,-40,70,140,95,50e',
    'v-relative-curve': 'm5,50v25,-90,65,90,90,0e',
    't-relative-move': 'm10,10l40,10t0,40l90,50e',
    'ar-arc': 'ar10,10,90,90,90,50,10,50e',
    'at-arcto': 'm50,90at10,10,90,90,50,90,90,50e',
    'wa-clockwise-arc': 'wa10,10,90,90,90,50,10,50e',
    'wr-clockwise-arcto': 'm50,90wr10,10,90,90,50,90,90,50e',
    'qx-qy-quadrants': 'm10,90qx50,10qy90,90xe',
    'qb-quadratic': 'm10,90qb50,-30,90,90e',
    'qb-starts-path': 'qb10,90,50,-30,90,90e',
    'al-angle-ellipse': 'al50,50,40,30,0,23592960e',
    'ae-angle-ellipse-to': 'm10,50ae50,50,40,30,11796480,11796480e',
    'nf-ns': 'm10,10l90,10,90,90,10,90xnfem20,30l80,30nse',
    'omitted-zeros': 'm,l100,,100,100,,100xm25,l75,v14,,25,12,25,25c100,39,89,50,75,50l25,50c12,50,,39,,25,,12,12,,25,xe',
    'two-subpaths-hole': 'm10,10l90,10,90,90,10,90xm30,30l30,70,70,70,70,30xe',
}
for name, path in PATHS.items():
    case(f'path-{name}', f'v:shape path="{path}"', para(shape(f'coordsize="100,100" path="{path}"', tag='v:shape')))

# --- preset shape types (Word's own shapetypes, with formulas and handles) ---------------------------------------
for spt in sorted(k for k in SHAPETYPES if k not in (32, 34, 75, 136, 202)):
    case(f'preset-{spt}', f'o:spt={spt}', para(typed(spt, shape(f'type="#_x0000_t{spt}"', tag='v:shape'))))

# --- stroke -------------------------------------------------------------------------------------------------------
def line(stroke: str = '', attrs: str = '', weight: str = '3pt') -> str:
    return para(pict(f'<v:line from="0,36pt" to="144pt,36pt" strokecolor="{STROKE}" strokeweight="{weight}" {attrs}>'
                     f'<v:stroke {stroke}/></v:line>'))


for w in ('0.25pt', '1pt', '6pt'):
    case(f'stroke-weight-{w}', f'strokeweight={w}', line(weight=w))
for d in ('solid', 'shortdash', 'shortdot', 'shortdashdot', 'shortdashdotdot', 'dot', 'dash', 'longdash', 'dashdot',
          'longdashdot', 'longdashdotdot', '1 1', '3 1', '4 2 1 2', '8 3 1 3 1 3'):
    case(f'stroke-dash-{d.replace(" ", "_")}', f'dashstyle="{d}"', line(f'dashstyle="{d}"'))
    case(f'rect-dash-{d.replace(" ", "_")}', f'v:rect dashstyle="{d}"', para(shape(inner=f'<v:stroke dashstyle="{d}"/>')))
for ls in ('single', 'thinThin', 'thinThick', 'thickThin', 'thickBetweenThin'):
    case(f'stroke-linestyle-{ls}', f'linestyle={ls}', line(f'linestyle="{ls}"', weight='6pt'))
for cap in ('flat', 'round', 'square'):
    case(f'stroke-endcap-{cap}', f'endcap={cap}', line(f'endcap="{cap}"', weight='12pt'))
for join in ('round', 'bevel', 'miter'):
    case(f'stroke-join-{join}', f'joinstyle={join}', para(pict(
        f'<v:polyline points="0,72pt,72pt,0,144pt,72pt" filled="f" strokecolor="{STROKE}" strokeweight="12pt">'
        f'<v:stroke joinstyle="{join}"/></v:polyline>')))
for arrow in ('block', 'classic', 'oval', 'diamond', 'open'):
    case(f'arrow-{arrow}', f'startarrow/endarrow={arrow}', line(f'startarrow="{arrow}" endarrow="{arrow}"', weight='1.5pt'))
for aw in ('narrow', 'medium', 'wide'):
    for al in ('short', 'long'):
        case(f'arrow-size-{aw}-{al}', f'endarrow=block {aw}/{al}',
             line(f'endarrow="block" endarrowwidth="{aw}" endarrowlength="{al}"', weight='1.5pt'))
for aw in ('narrow', 'wide'):
    for al in ('short', 'long'):
        case(f'arrow-start-size-{aw}-{al}', f'startarrow=classic {aw}/{al}',
             line(f'startarrow="classic" startarrowwidth="{aw}" startarrowlength="{al}"', weight='1.5pt'))
case('arrow-on-path', 'arrows on an open v:shape path', para(shape(
    'coordsize="100,100" path="m5,90c30,-40,70,140,95,10e" filled="f"', '<v:stroke startarrow="oval" endarrow="classic"/>',
    tag='v:shape')))
case('stroke-off', 'stroked=f', para(shape('stroked="f"')))
case('stroke-opacity', 'stroke opacity=50%', line('opacity="0.5"', weight='12pt'))
case('stroke-color', 'stroke color=red', line('color="#c00000"'))

# --- fill ---------------------------------------------------------------------------------------------------------
case('fill-none', 'filled=f', para(shape('filled="f"')))
case('fill-opacity', 'fill opacity=40%', para(shape(inner='<v:fill opacity="0.4"/>')))
for angle in (0, 45, 90, -135):
    case(f'fill-gradient-{angle}', f'gradient angle={angle}', para(shape(
        inner=f'<v:fill type="gradient" color2="#c00000" angle="{angle}"/>')))
case('fill-gradient-focus', 'gradient focus=50% (reflected)', para(shape(inner='<v:fill type="gradient" color2="#c00000" focus="50%"/>')))
case('fill-gradient-colors', 'gradient colors="0 …;.5 …;1 …"', para(shape(
    inner='<v:fill type="gradient" colors="0 #ffc000;.5 #00b050;1 #7030a0" angle="90"/>')))
case('fill-gradient-radial', 'gradientRadial focusposition=.5,.5', para(shape(
    inner='<v:fill type="gradientRadial" color2="#c00000" focusposition=".5,.5" focussize="0,0"/>')))
case('fill-gradient-opacity2', 'gradient o:opacity2', para(shape(
    inner='<v:fill type="gradient" color2="#c00000" o:opacity2="0.1" angle="90"/>')))
# Word's own bitmap for the wdUpDiag preset (word-wdUpDiag.gif, as Word writes it), and one that is no preset
case('fill-pattern', 'type=pattern, Word bitmap (wdUpDiag), black on white', para(shape(
    'fillcolor="#000000"', '<v:fill r:id="rIdPattern" o:title="" color2="#ffffff" type="pattern"/>')))
case('fill-pattern-colored', 'type=pattern, Word bitmap (wdUpDiag), red on yellow', para(shape(
    'fillcolor="#c00000"', '<v:fill r:id="rIdPattern" o:title="" color2="#ffff00" type="pattern"/>')))
case('fill-pattern-custom', 'type=pattern, a bitmap that is no Word preset', para(shape(
    'fillcolor="#c00000"', '<v:fill r:id="rIdHatch" o:title="" color2="#ffff00" type="pattern"/>')))
case('fill-tile', 'type=tile', para(shape(inner='<v:fill r:id="rIdPhoto" o:title="photo" type="tile"/>')))
for dpi in (72, 96, 300):
    case(f'fill-tile-{dpi}dpi', f'type=tile, picture stating {dpi} dpi', para(shape(
        inner=f'<v:fill r:id="rIdPhoto{dpi}" o:title="photo" type="tile"/>', size='width:288pt;height:72pt')))
case('fill-frame', 'type=frame (stretched picture)', para(shape(inner='<v:fill r:id="rIdPhoto" o:title="photo" type="frame"/>')))

# --- transforms ---------------------------------------------------------------------------------------------------
ARROW = 13   # right arrow: shows rotation and flips
def arrow(style: str) -> str:
    return para(typed(ARROW, shape(f'type="#_x0000_t{ARROW}"', tag='v:shape', style=style)))


for rot in ('30', '90', '-90', '180', '315', '-90.0014'):
    case(f'rotation-{rot}', f'rotation:{rot}', arrow(f'rotation:{rot}'))
for flip in ('x', 'y', 'x y'):
    case(f'flip-{flip.replace(" ", "")}', f'flip:{flip}', arrow(f'flip:{flip}'))
case('rotation-flip', 'rotation:45;flip:x', arrow('rotation:45;flip:x'))


def group(children: str, style: str = 'width:216pt;height:108pt', attrs: str = 'coordorigin="0,0" coordsize="2160,1080"') -> str:
    return pict(f'<v:group style="{style}" {attrs}>{children}</v:group>')


KIDS = (f'<v:rect style="position:absolute;left:0;top:0;width:900;height:500" fillcolor="{FILL}" strokecolor="{STROKE}"/>'
        f'<v:oval style="position:absolute;left:1000;top:300;width:1100;height:700" fillcolor="#f4cccc" strokecolor="{STROKE}"/>'
        f'<v:shape type="#_x0000_t{ARROW}" style="position:absolute;left:100;top:600;width:800;height:400" fillcolor="#b6d7a8" strokecolor="{STROKE}"/>')
case('group-basic', 'v:group coordsize, three children', para(group(KIDS)))
case('group-coordorigin-x-only', 'child group coordorigin="1000" (y omitted, as Word writes a zero)', para(group(
    f'<v:rect style="position:absolute;left:0;top:0;width:2160;height:1080" filled="f" strokecolor="{STROKE}"/>'
    f'<v:group style="position:absolute;left:1000;width:1000;height:1080" coordorigin="1000" coordsize="1000,1080">'
    f'<v:rect style="position:absolute;left:1100;top:100;width:800;height:800" fillcolor="{FILL}" strokecolor="{STROKE}"/></v:group>')))
case('group-coordorigin', 'v:group coordorigin=-500,-200', para(group(KIDS, attrs='coordorigin="-500,-200" coordsize="2660,1280"')))
case('group-rotation', 'v:group rotation:20', para(group(KIDS, style='width:216pt;height:108pt;rotation:20')))
case('group-flip', 'v:group flip:x', para(group(KIDS, style='width:216pt;height:108pt;flip:x')))
case('group-nested', 'group inside group, inner coordsize differs', para(group(
    KIDS[:KIDS.index('<v:oval')] + '<v:group style="position:absolute;left:1000;top:0;width:1100;height:1080" '
    f'coordorigin="0,0" coordsize="100,100"><v:oval style="position:absolute;left:0;top:0;width:100;height:50" '
    f'fillcolor="#f4cccc" strokecolor="{STROKE}"/><v:rect style="position:absolute;left:25;top:60;width:50;height:40;'
    f'rotation:30" fillcolor="#ffe599" strokecolor="{STROKE}"/></v:group>')))
case('group-child-rotation', 'rotated child in group', para(group(
    f'<v:rect style="position:absolute;left:400;top:200;width:1200;height:600;rotation:30" fillcolor="{FILL}" strokecolor="{STROKE}"/>')))
case('group-child-line', 'v:line in group (from/to in group coordinates)', para(group(
    f'<v:line style="position:absolute" from="100,100" to="2000,1000" strokecolor="{STROKE}" strokeweight="2pt">'
    '<v:stroke endarrow="block"/></v:line>')))

# --- text boxes ---------------------------------------------------------------------------------------------------
def textbox(text: str = 'Resource block', tb_style: str = '', shape_style: str = '', inset: str = '', size: str = 'width:144pt;height:72pt', jc: str = '') -> str:
    ppr = f'<w:pPr><w:jc w:val="{jc}"/></w:pPr>' if jc else ''
    tb = (f'<v:textbox{f" style={chr(34)}{tb_style}{chr(34)}" if tb_style else ""}{f" inset={chr(34)}{inset}{chr(34)}" if inset else ""}>'
          f'<w:txbxContent><w:p>{ppr}<w:r><w:t>{escape(text)}</w:t></w:r></w:p></w:txbxContent></v:textbox>')
    return para(typed(202, shape('type="#_x0000_t202"', tb, tag='v:shape', size=size, style=shape_style)))


case('textbox-plain', 'text box', textbox())
case('textbox-inset', 'inset=20pt,2pt,2pt,2pt', textbox(inset='20pt,2pt,2pt,2pt'))
case('textbox-center', 'centred paragraph', textbox(jc='center'))
for flow in ('horizontal', 'vertical', 'vertical-ideographic', 'horizontal-ideographic'):
    case(f'textbox-flow-{flow}', f'layout-flow:{flow}', textbox(tb_style=f'layout-flow:{flow}', size='width:36pt;height:144pt'))
for alt in ('bottom-to-top', 'top-to-bottom'):
    case(f'textbox-flow-alt-{alt}', f'layout-flow:vertical;mso-layout-flow-alt:{alt}',
         textbox(tb_style=f'layout-flow:vertical;mso-layout-flow-alt:{alt}', size='width:36pt;height:144pt'))
for anchor in ('top', 'middle', 'bottom'):
    case(f'textbox-anchor-{anchor}', f'v-text-anchor:{anchor}', textbox(shape_style=f'v-text-anchor:{anchor}', size='width:144pt;height:108pt'))
case('textbox-rotated', 'text box rotation:90', textbox(shape_style='rotation:90'))
case('textbox-fit', 'mso-fit-shape-to-text:t', textbox('Fits its text', tb_style='mso-fit-shape-to-text:t'))
case('textbox-in-group', 'vertical text box in group', para(group(
    f'<v:rect style="position:absolute;left:0;top:0;width:2160;height:1080" filled="f" strokecolor="{STROKE}"/>'
    f'<v:shape type="#_x0000_t202" style="position:absolute;left:100;top:50;width:300;height:1000" filled="f" stroked="f">'
    '<v:textbox style="layout-flow:vertical-ideographic" inset="0,0,0,0"><w:txbxContent><w:p><w:r><w:t>Lower Edge</w:t>'
    '</w:r></w:p></w:txbxContent></v:textbox></v:shape>')))

# --- shadow, text path, pictures ----------------------------------------------------------------------------------
case('shadow', 'v:shadow on offset 4pt', para(shape(inner='<v:shadow on="t" color="#7f7f7f" offset="4pt,4pt"/>')))
case('shadow-opacity', 'v:shadow opacity 50%', para(shape(inner='<v:shadow on="t" color="#000000" opacity="0.5" offset="6pt,6pt"/>')))
case('textpath', 'v:textpath (WordArt)', para(typed(136, shape('type="#_x0000_t136"', '<v:path textpathok="t"/>'
     '<v:textpath on="t" fitshape="t" string="Sub block"/>', tag='v:shape'))))
case('imagedata', 'picture frame v:imagedata', para(typed(75, shape('type="#_x0000_t75" stroked="f"', '<v:imagedata r:id="rIdPhoto" o:title=""/>', tag='v:shape'))))
case('imagedata-crop', 'imagedata croptop/cropleft 25%', para(shape(
    'type="#_x0000_t75" stroked="f"', '<v:imagedata r:id="rIdPhoto" o:title="" croptop="16384f" cropleft="16384f"/>', tag='v:shape')))
case('imagedata-gray', 'imagedata grayscale', para(shape(
    'type="#_x0000_t75" stroked="f"', '<v:imagedata r:id="rIdPhoto" o:title="" grayscale="t"/>', tag='v:shape')))

# --- floating placement --------------------------------------------------------------------------------------------
FLOAT = 'position:absolute;mso-position-horizontal-relative:text;mso-position-vertical-relative:text'
def floating(left: float, top: float, w: float, h: float, z: int, tag: str = 'v:rect', attrs: str = '', inner: str = '') -> str:
    return pict(f'<{tag} style="{FLOAT};margin-left:{left}pt;margin-top:{top}pt;width:{w}pt;height:{h}pt;z-index:{z}" '
                f'{"" if "fillcolor=" in attrs else f"fillcolor={chr(34)}{FILL}{chr(34)} "}strokecolor="{STROKE}" {attrs}>{inner}</{tag}>')


SPACER = '<w:pPr><w:spacing w:after="2400"/></w:pPr>'
case('float-pieces', 'five floating pieces in one paragraph form one figure', f'<w:p>{SPACER}' + ''.join(
    f'<w:r>{floating(20 + i * 30, 10, 26, 80, i + 1)}</w:r>' for i in range(4)) +
    f'<w:r>{pict(f"<v:line style={chr(34)}{FLOAT};z-index:9{chr(34)} from={chr(34)}0,95pt{chr(34)} to={chr(34)}160pt,95pt{chr(34)} strokecolor={chr(34)}{STROKE}{chr(34)} strokeweight={chr(34)}2pt{chr(34)}><v:stroke endarrow={chr(34)}block{chr(34)}/></v:line>")}</w:r></w:p>')
case('float-zorder', 'overlapping, z-index decides which is on top', f'<w:p>{SPACER}<w:r>' + floating(20, 10, 100, 60, 2) +
     '</w:r><w:r>' + floating(60, 40, 100, 60, 1, attrs='fillcolor="#f4cccc"') + '</w:r></w:p>')
case('float-behind-text', 'negative z-index, behind text', f'<w:p>{SPACER}<w:r>' + floating(0, 0, 200, 40, -1, attrs='fillcolor="#ffe599"') +
     '</w:r><w:r><w:t>Text over a floating rectangle.</w:t></w:r></w:p>')
case('float-two-paragraphs', 'one figure anchored in two paragraphs', f'<w:p><w:r>' + floating(20, 0, 100, 40, 1) +
     '</w:r></w:p><w:p><w:pPr><w:spacing w:after="1600"/></w:pPr><w:r>' + floating(80, 10, 100, 40, 2, attrs='fillcolor="#f4cccc"') + '</w:r></w:p>')
case('float-relative-margin', 'mso-position-horizontal-relative:margin', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="position:absolute;margin-left:200pt;margin-top:10pt;width:100pt;height:50pt;z-index:1;'
    f'mso-position-horizontal-relative:margin;mso-position-vertical-relative:text" fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r></w:p>')

for rot in ('60', '90', '120'):
    case(f'float-rotation-{rot}', f'floating arrow rotation:{rot}', f'<w:p>{SPACER}<w:r>' + typed(ARROW, pict(
        f'<v:shape type="#_x0000_t{ARROW}" style="{FLOAT};margin-left:40pt;margin-top:30pt;width:144pt;height:72pt;z-index:1;'
        f'rotation:{rot}" fillcolor="{FILL}" strokecolor="{STROKE}"/>')) + '</w:r></w:p>')
    case(f'group-child-rotation-{rot}', f'arrow in a group, rotation:{rot}', para(group(
        f'<v:shape type="#_x0000_t{ARROW}" style="position:absolute;left:400;top:200;width:1200;height:600;rotation:{rot}" '
        f'fillcolor="{FILL}" strokecolor="{STROKE}"/>')))

# --- found in 3GPP specifications (vml_inventory.py over 4838 spec .docx) -----------------------------------------
case('float-page-relative', 'mso-position-horizontal/vertical-relative:page', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="position:absolute;margin-left:300pt;margin-top:300pt;width:100pt;height:50pt;z-index:1;'
    f'mso-position-horizontal-relative:page;mso-position-vertical-relative:page" fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r></w:p>')
case('float-position-center', 'mso-position-horizontal:center relative to the margin', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="position:absolute;margin-left:0;margin-top:20pt;width:100pt;height:50pt;z-index:1;'
    f'mso-position-horizontal:center;mso-position-horizontal-relative:margin;mso-position-vertical-relative:text" '
    f'fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r></w:p>')
case('float-percent-size', 'mso-width-percent:500 of the margin', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="position:absolute;margin-left:0;margin-top:20pt;width:100pt;height:50pt;z-index:1;'
    f'mso-width-percent:500;mso-width-relative:margin;mso-position-horizontal-relative:margin;'
    f'mso-position-vertical-relative:text" fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r></w:p>')
case('imagedata-chromakey', 'picture with chromakey=white over a red rectangle', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="{FLOAT};margin-left:0;margin-top:0;width:160pt;height:80pt;z-index:1" fillcolor="#c00000" stroked="f"/>') +
    '</w:r><w:r>' + typed(75, pict(f'<v:shape type="#_x0000_t75" style="{FLOAT};margin-left:10pt;margin-top:10pt;width:144pt;height:72pt;'
    'z-index:2"><v:imagedata r:id="rIdPhoto" o:title="" chromakey="white"/></v:shape>')) + '</w:r></w:p>')
case('imagedata-crop-right-bottom', 'imagedata cropright/cropbottom 25%', para(shape(
    'type="#_x0000_t75" stroked="f"', '<v:imagedata r:id="rIdPhoto" o:title="" cropright="16384f" cropbottom="16384f"/>', tag='v:shape')))
case('line-flip', 'v:line style flip:y, connector straight', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:line style="position:absolute;flip:y;z-index:1;mso-position-horizontal-relative:text;mso-position-vertical-relative:text" '
    f'from="20pt,10pt" to="160pt,80pt" o:connectortype="straight" strokecolor="{STROKE}" strokeweight="2pt"><v:stroke endarrow="block"/></v:line>')
    + '</w:r></w:p>')
case('line-rotation', 'v:line style rotation:30', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:line style="position:absolute;rotation:30;z-index:1;mso-position-horizontal-relative:text;mso-position-vertical-relative:text" '
    f'from="20pt,40pt" to="160pt,40pt" strokecolor="{STROKE}" strokeweight="2pt"><v:stroke endarrow="block"/></v:line>') + '</w:r></w:p>')
case('group-canvas', 'v:group editas=canvas (a drawing canvas)', para(pict(
    f'<v:group style="width:216pt;height:108pt;mso-position-horizontal-relative:char;mso-position-vertical-relative:line" '
    f'coordorigin="0,0" coordsize="2160,1080" editas="canvas"><o:lock v:ext="edit" aspectratio="t"/>'
    f'<v:shape type="#_x0000_t75" style="position:absolute;width:2160;height:1080" o:preferrelative="f"><v:fill o:detectmouseclick="t"/>'
    f'<v:path o:extrusionok="t" o:connecttype="none"/></v:shape>{KIDS}</v:group>')))
case('textbox-linked', 'two text boxes linked by mso-next-textbox', f'<w:p>{SPACER}<w:r>' + typed(202, pict(
    f'<v:shape id="tbA" type="#_x0000_t202" style="{FLOAT};margin-left:0;margin-top:0;width:100pt;height:30pt;z-index:1" '
    f'fillcolor="{FILL}" strokecolor="{STROKE}"><v:textbox style="mso-next-textbox:#tbB"><w:txbxContent><w:p><w:r><w:t>'
    'One two three four five six seven eight nine ten eleven twelve</w:t></w:r></w:p></w:txbxContent></v:textbox></v:shape>')) +
    '</w:r><w:r>' + pict(f'<v:shape id="tbB" type="#_x0000_t202" style="{FLOAT};margin-left:150pt;margin-top:0;width:100pt;height:60pt;'
    f'z-index:2" fillcolor="#f4cccc" strokecolor="{STROKE}"><v:textbox/></v:shape>') + '</w:r></w:p>')
case('shape-spt100', 'v:shape o:spt=100 (a freeform) with its own path', para(shape(
    'o:spt="100" coordsize="21600,21600" path="m,21600l10800,,21600,21600,10800,14400xe"', tag='v:shape')))
case('group-spt100', 'freeform o:spt=100 with its own path inside a group', para(group(
    f'<v:rect style="position:absolute;left:0;top:0;width:2160;height:1080" filled="f" strokecolor="{STROKE}"/>'
    f'<v:shape style="position:absolute;left:200;top:200;width:1600;height:700" o:spt="100" adj="0,,0" coordsize="1600,700" '
    f'path="m,700l800,,1600,700xe" fillcolor="{FILL}" strokecolor="{STROKE}"><v:formulas/><v:path arrowok="t" o:connecttype="segments"/></v:shape>')))
case('float-wrap-top-bottom', 'w10:wrap type=topAndBottom between two paragraphs', '<w:p><w:r><w:t>Text before the shape.</w:t></w:r>'
    '<w:r>' + pict(f'<v:rect style="position:absolute;margin-left:20pt;margin-top:16pt;width:100pt;height:50pt;z-index:1;'
    f'mso-position-horizontal-relative:text;mso-position-vertical-relative:text" fillcolor="{FILL}" strokecolor="{STROKE}">'
    '<w10:wrap type="topAndBottom"/></v:rect>') + '</w:r></w:p><w:p><w:r><w:t>Text after the shape.</w:t></w:r></w:p>')
case('imagedata-linked-and-embedded', 'imagedata with r:id and an r:href to a missing file', para(shape(
    'type="#_x0000_t75" stroked="f"', '<v:imagedata r:id="rIdPhoto" r:href="rIdLink" o:title=""/>', tag='v:shape')))

# --- found in TDocs (vml_inventory.py over 4000 TDoc .docx and 600 .doc) -------------------------------------------
for c in ('windowText', 'window', 'buttonFace', 'buttonShadow', 'highlight', 'grayText', 'infoBackground', 'threeDShadow'):
    case(f'syscolor-{c}', f'system colour {c} as fill (a rectangle) and stroke (the next one)', para(
        pict(f'<v:rect style="width:100pt;height:50pt" fillcolor="{c}" strokecolor="windowText" strokeweight="3pt"/>')
        + '</w:r><w:r>' + pict(f'<v:rect style="width:100pt;height:50pt" filled="f" strokecolor="{c}" strokeweight="6pt"/>')))
case('fill-child-off', 'v:fill on="f"', para(shape(inner='<v:fill on="f"/>')))
case('stroke-child-off', 'v:stroke on="f"', para(shape(inner='<v:stroke on="f"/>')))
case('float-hidden', 'visibility:hidden (Word draws nothing)', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="{FLOAT};margin-left:20pt;margin-top:20pt;width:100pt;height:50pt;z-index:1;visibility:hidden" '
    f'fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r><w:r><w:t>Only this text.</w:t></w:r></w:p>')
for h, v in (('right', 'top'), ('left', 'bottom')):
    case(f'float-align-{h}-{v}', f'mso-position-horizontal:{h};mso-position-vertical:{v} (margin)', f'<w:p>{SPACER}<w:r>' + pict(
        f'<v:rect style="position:absolute;margin-left:0;margin-top:0;width:100pt;height:50pt;z-index:1;'
        f'mso-position-horizontal:{h};mso-position-horizontal-relative:margin;mso-position-vertical:{v};'
        f'mso-position-vertical-relative:margin" fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r></w:p>')
case('float-percent-position', 'mso-left-percent:400;mso-top-percent:300 of the page', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:rect style="position:absolute;margin-left:0;margin-top:0;width:100pt;height:50pt;z-index:1;mso-left-percent:400;'
    f'mso-top-percent:300;mso-position-horizontal-relative:page;mso-position-vertical-relative:page" '
    f'fillcolor="{FILL}" strokecolor="{STROKE}"/>') + '</w:r></w:p>')
case('rect-hr', 'v:rect o:hr (horizontal rule)', para(pict(
    '<v:rect style="width:0;height:1.5pt" o:hralign="center" o:hrstd="t" o:hr="t" fillcolor="#a0a0a0" stroked="f"/>')))
case('oval-rotation', 'v:oval rotation:30', para(shape(tag='v:oval', size='width:144pt;height:72pt;rotation:30')))
case('stroke-miterlimit', 'joinstyle=miter miterlimit=2 on a sharp angle', para(pict(
    f'<v:polyline points="0,72pt,20pt,0,40pt,72pt" filled="f" strokecolor="{STROKE}" strokeweight="8pt">'
    '<v:stroke joinstyle="miter" miterlimit="2"/></v:polyline>')))
case('ole-tool-type', 'picture-frame shapetype with a bogus o:spt and type without "#" (a non-Word writer)', para(
    '<w:pict>' + '<v:shapetype id="_x0000_tole_rId8" coordsize="21600,21600" o:spt="8" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f"><v:stroke joinstyle="miter"/><v:formulas><v:f eqn="if lineDrawn pixelLineWidth 0"/><v:f eqn="sum @0 1 0"/><v:f eqn="sum 0 0 @1"/><v:f eqn="prod @2 1 2"/><v:f eqn="prod @3 21600 pixelWidth"/><v:f eqn="prod @3 21600 pixelHeight"/><v:f eqn="sum @0 0 1"/><v:f eqn="prod @6 1 2"/><v:f eqn="prod @7 21600 pixelWidth"/><v:f eqn="sum @8 21600 0"/><v:f eqn="prod @7 21600 pixelHeight"/><v:f eqn="sum @10 21600 0"/></v:formulas><v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/><o:lock v:ext="edit" aspectratio="t"/></v:shapetype>' + '<v:shape type="_x0000_tole_rId8" style="width:144pt;height:72pt" filled="f">'
    '<v:imagedata r:id="rIdPhoto" o:title=""/></v:shape></w:pict>'))

# --- connectors ---------------------------------------------------------------------------------------------------
case('connector-straight', 'o:spt=32 straight connector with arrow', para(typed(32, pict(
    f'<v:shape type="#_x0000_t32" style="width:144pt;height:72pt" o:connectortype="straight" strokecolor="{STROKE}" '
    'strokeweight="1.5pt"><v:stroke endarrow="block"/></v:shape>'))))
case('connector-elbow', 'o:spt=34 elbow connector', para(typed(34, pict(
    f'<v:shape type="#_x0000_t34" style="width:144pt;height:72pt" o:connectortype="elbow" adj="5400" strokecolor="{STROKE}" '
    'strokeweight="1.5pt"><v:stroke endarrow="block"/></v:shape>'))))
case('connector-float-vertical', 'floating straight connector, width 0, flip:y, arrow (TS 38.521-4)', f'<w:p>{SPACER}<w:r>' + pict(
    f'<v:shape type="#_x0000_t32" style="position:absolute;flip:y;margin-left:60pt;margin-top:10pt;width:0;height:60pt;z-index:1;'
    f'mso-position-horizontal-relative:text;mso-position-vertical-relative:text" o:connectortype="straight" strokecolor="{STROKE}" '
    'strokeweight="1pt" filled="f"><v:stroke endarrow="block"/></v:shape>') + '</w:r></w:p>')
case('connector-flip', 'straight connector flip:y', para(pict(
    f'<v:shape type="#_x0000_t32" style="width:144pt;height:72pt;flip:y" o:connectortype="straight" strokecolor="{STROKE}" '
    'strokeweight="1.5pt"><v:stroke endarrow="block"/></v:shape>')))


# --- package ------------------------------------------------------------------------------------------------------
def png(image: Image.Image, dpi: int | None = None) -> bytes:
    out = io.BytesIO()
    image.save(out, 'PNG', **({'dpi': (dpi, dpi)} if dpi else {}))
    return out.getvalue()


hatch = Image.new('1', (8, 8), 1)
for i in range(8):
    hatch.putpixel(((i + 1) % 8, 7 - i), 0)
    hatch.putpixel(((i + 2) % 8, 7 - i), 0)
photo = Image.new('RGB', (96, 48), '#ffffff')
draw = ImageDraw.Draw(photo)
draw.rectangle((0, 0, 47, 23), fill='#c00000')
draw.rectangle((48, 0, 95, 23), fill='#00b050')
draw.rectangle((0, 24, 47, 47), fill='#0070c0')
draw.ellipse((56, 28, 88, 46), fill='#ffc000')

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:v="urn:schemas-microsoft-com:vml" '
      'xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w10="urn:schemas-microsoft-com:office:word" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
body = BREAK.join(f'<w:p><w:r><w:t xml:space="preserve">[case {cid}] {escape(desc)}</w:t></w:r></w:p>{xml}' for cid, desc, xml in cases)
document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}'
            '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
            'w:header="709" w:footer="709" w:gutter="0"/></w:sectPr></w:body></w:document>')
parts = {
    '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/><Default Extension="gif" ContentType="image/gif"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
    '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
    'word/_rels/document.xml.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        + ''.join(f'<Relationship Id="rIdPhoto{d}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/photo{d}.png"/>' for d in (72, 96, 300)) +
        '<Relationship Id="rIdLink" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="file:///missing/photo.png" TargetMode="External"/>'
        '<Relationship Id="rIdPattern" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/pattern.gif"/>'
        '<Relationship Id="rIdHatch" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/hatch.png"/>'
        '<Relationship Id="rIdPhoto" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/photo.png"/></Relationships>',
    'word/document.xml': document,
    'word/styles.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/><w:sz w:val="20"/>'
        '<w:szCs w:val="20"/><w:lang w:val="en-GB"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" '
        'w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/></w:style></w:styles>',
}
with zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in parts.items():
        z.writestr(name, data)
    z.writestr('word/media/hatch.png', png(hatch))
    for d in (72, 96, 300):
        z.writestr(f'word/media/photo{d}.png', png(photo, d))
    z.writestr('word/media/pattern.gif', (HERE / 'word-wdUpDiag.gif').read_bytes())
    z.writestr('word/media/photo.png', png(photo))
# Cases not judged on a path, with the reason (the reference itself is inconsistent there)
MAC_SYSCOLOR = 'Word for Mac draws system colours in macOS values; specDuck keeps the Windows defaults, as authors see them'
SKIP = {
    'rect-hr': {'docword': 'Word draws its own horizontal rule back from .doc as a vertical line',
                'docx2t': 'Word draws its own horizontal rule back from .doc as a vertical line'},
    **{f'syscolor-{c}': {'*': MAC_SYSCOLOR} for c in ('buttonFace', 'buttonShadow', 'highlight', 'grayText', 'infoBackground', 'threeDShadow')},
    'path-qb-quadratic': {'*': 'Word draws nothing for qb after an m (qb-starts-path covers qb)'},
    'stroke-dash-4_2_1_2': {'docword': 'Word saves "4 2 1 2" to .doc as dashSys like "3 1", then draws only this one solid',
                            'docx2t': 'Word saves "4 2 1 2" to .doc as dashSys like "3 1", then draws only this one solid'},
    'rect-dash-4_2_1_2': {'docword': 'Word saves "4 2 1 2" to .doc as dashSys like "3 1", then draws only this one solid',
                          'docx2t': 'Word saves "4 2 1 2" to .doc as dashSys like "3 1", then draws only this one solid'},
}
json.dump([{'id': c, 'desc': d, **({'skip': SKIP[c]} if c in SKIP else {})} for c, d, _ in cases], open(Path(sys.argv[1]).with_suffix('.cases.json'), 'w'), indent=0)
print(len(cases), 'cases')
