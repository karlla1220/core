"""Write WordPresetGeometry.h from adjfit.json (fit_adj.py) and spt2prst.json: a legacy shape in its Word built-in
look as the DrawingML preset Word gives it, with Word's VML-adj -> avLst conversion."""
import json
import sys

fit = json.load(open('adjfit.json'))
names = json.load(open('spt2prst.json'))
FORMS = ['1', 'w/ss', 'h/ss', 'ss/w', 'ss/h', 'w/h', 'h/w']
FORMS += ['*' + f for f in FORMS]
rows = []
for spt, (prst, *_rest) in sorted(((k, v) for k, v in names.items() if k.isdigit() and k in fit), key=lambda kv: int(kv[0])):
    gds = fit[spt]['gd']
    if fit[spt]['prst'] != prst:
        sys.exit(f'{spt}: {prst} vs {fit[spt]["prst"]}')
    guides = ', '.join(f'{{L"{g}", {i}, {FORMS.index(form)}, {a}, {b}}}' for g, (i, form, a, b) in sorted(gds.items()))
    rows.append(f'\t\t\t{{{spt}, {{L"{prst}", {{{guides}}}}}}},')
out = f'''/* specduck: Word's DrawingML preset for each legacy shape type in its built-in look, and how Word turns the VML adj
 * values into the preset's guides (fitted from shapes Word itself made: specduck/tests/vml/fit_adj.py). A guide is
 * a * adj[index] * F + b, or (a * adj[index] + b) * F for a form marked scaled, F one of 1, w/ss, h/ss, ss/w, ss/h,
 * w/h, h/w (w, h the shape's size, ss the shorter); index -1 is the constant b. */
#pragma once
#include <algorithm>
#include <cmath>
#include <map>
#include <string>
#include <vector>

namespace NSBinPptxRW
{{
	struct WordPresetGuide {{ const wchar_t* name; int adj; int form; double a; double b; }};
	struct WordPreset {{ const wchar_t* prst; std::vector<WordPresetGuide> guides; }};

	inline const std::map<unsigned int, WordPreset>& WordPresets()
	{{
		static const std::map<unsigned int, WordPreset> presets = {{
{chr(10).join(rows)}
		}};
		return presets;
	}}

	// The a:prstGeom for a shape of legacy type spt (adj: its VML adj values; w, h: its size in any one unit), or ""
	inline std::wstring WordPresetGeometry(unsigned int spt, const std::vector<long>& adj, double w, double h)
	{{
		std::map<unsigned int, WordPreset>::const_iterator it = WordPresets().find(spt);
		if (it == WordPresets().end())
			return L"";
		if (w <= 0 || h <= 0) w = h = 1;
		double ss = (std::min)(w, h);
		const double forms[] = {{1, w / ss, h / ss, ss / w, ss / h, w / h, h / w}};
		std::wstring av;
		for (const WordPresetGuide& g : it->second.guides)
		{{
			if (g.adj >= (int)adj.size())
				continue;
			double x = g.adj < 0 ? 0 : adj[g.adj];
			long v = g.form >= 7 ? (long)std::lround((g.a * x + g.b) * forms[g.form - 7])
								 : (long)std::lround(g.a * x * forms[g.form] + g.b);
			av += L"<a:gd name=\\"" + std::wstring(g.name) + L"\\" fmla=\\"val " + std::to_wstring(v) + L"\\"/>";
		}}
		return L"<a:prstGeom xmlns:a=\\"http://schemas.openxmlformats.org/drawingml/2006/main\\" prst=\\""
			+ std::wstring(it->second.prst) + L"\\"><a:avLst>" + av + L"</a:avLst></a:prstGeom>";
	}}
}}
'''
open(sys.argv[1], 'w').write(out)
print(len(rows), 'presets')
