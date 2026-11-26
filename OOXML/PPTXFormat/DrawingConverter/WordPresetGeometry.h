/* specduck: Word's DrawingML preset for each legacy shape type in its built-in look, and how Word turns the VML adj
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
{
	struct WordPresetGuide { const wchar_t* name; int adj; int form; double a; double b; };
	struct WordPreset { const wchar_t* prst; std::vector<WordPresetGuide> guides; };

	inline const std::map<unsigned int, WordPreset>& WordPresets()
	{
		static const std::map<unsigned int, WordPreset> presets = {
			{4, {L"diamond", {}}},
			{5, {L"triangle", {{L"adj", 0, 0, 4.62963, 0.0}}}},
			{6, {L"rtTriangle", {}}},
			{7, {L"parallelogram", {{L"adj", 0, 8, 4.62963, 0.0}}}},
			{10, {L"octagon", {{L"adj", 0, 0, 4.629917, -0.9}}}},
			{11, {L"plus", {{L"adj", 0, 0, 4.62963, -0.0}}}},
			{13, {L"rightArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 8, -4.62963, 100000.0}}}},
			{15, {L"homePlate", {{L"adj", 0, 8, -4.62963, 100000.0}}}},
			{16, {L"cube", {{L"adj", 0, 0, 4.62963, -0.0}}}},
			{21, {L"plaque", {{L"adj", 0, 0, 4.629585, 0.3}}}},
			{22, {L"can", {{L"adj", 0, 9, 4.62963, 0.0}}}},
			{23, {L"donut", {{L"adj", 0, 8, 4.62963, 0.0}}}},
			{41, {L"callout1", {{L"adj1", 3, 0, 4.62963, 0.0}, {L"adj2", 2, 0, 4.629583, 0.2}, {L"adj3", 1, 0, 4.62963, 0.0}, {L"adj4", 0, 0, 4.629605, 0.1}}}},
			{44, {L"accentCallout1", {{L"adj1", 3, 0, 4.62963, 0.0}, {L"adj2", 2, 0, 4.629583, 0.2}, {L"adj3", 1, 0, 4.62963, 0.0}, {L"adj4", 0, 0, 4.629605, 0.1}}}},
			{46, {L"accentCallout3", {{L"adj1", 7, 0, 4.62963, 0.0}, {L"adj2", 6, 0, 4.629583, 0.2}, {L"adj3", 5, 0, 4.62963, 0.0}, {L"adj4", 4, 0, 4.629667, -0.2}, {L"adj5", 3, 0, 4.62963, 0.0}, {L"adj6", 2, 0, 4.629667, -0.2}, {L"adj7", 1, 0, 4.629632, -0.0}, {L"adj8", 0, 0, 4.629583, 0.2}}}},
			{47, {L"borderCallout1", {{L"adj1", 3, 0, 4.62963, 0.0}, {L"adj2", 2, 0, 4.629583, 0.2}, {L"adj3", 1, 0, 4.62963, 0.0}, {L"adj4", 0, 0, 4.629605, 0.1}}}},
			{48, {L"borderCallout2", {{L"adj1", 5, 0, 4.62963, 0.0}, {L"adj2", 4, 0, 4.629583, 0.2}, {L"adj3", 3, 0, 4.62963, 0.0}, {L"adj4", 2, 0, 4.629667, -0.2}, {L"adj5", 1, 0, 4.62963, 0.0}, {L"adj6", 0, 0, 4.629652, -0.1}}}},
			{49, {L"borderCallout3", {{L"adj1", 7, 0, 4.62963, 0.0}, {L"adj2", 6, 0, 4.629583, 0.2}, {L"adj3", 5, 0, 4.62963, 0.0}, {L"adj4", 4, 0, 4.629667, -0.2}, {L"adj5", 3, 0, 4.62963, 0.0}, {L"adj6", 2, 0, 4.629667, -0.2}, {L"adj7", 1, 0, 4.629632, -0.0}, {L"adj8", 0, 0, 4.629583, 0.2}}}},
			{50, {L"accentBorderCallout1", {{L"adj1", 3, 0, 4.62963, 0.0}, {L"adj2", 2, 0, 4.629583, 0.2}, {L"adj3", 1, 0, 4.62963, 0.0}, {L"adj4", 0, 0, 4.629605, 0.1}}}},
			{51, {L"accentBorderCallout2", {{L"adj1", 5, 0, 4.62963, 0.0}, {L"adj2", 4, 0, 4.629583, 0.2}, {L"adj3", 3, 0, 4.62963, 0.0}, {L"adj4", 2, 0, 4.629667, -0.2}, {L"adj5", 1, 0, 4.62963, 0.0}, {L"adj6", 0, 0, 4.629652, -0.1}}}},
			{52, {L"accentBorderCallout3", {{L"adj1", 7, 0, 4.62963, 0.0}, {L"adj2", 6, 0, 4.629583, 0.2}, {L"adj3", 5, 0, 4.62963, 0.0}, {L"adj4", 4, 0, 4.629667, -0.2}, {L"adj5", 3, 0, 4.62963, 0.0}, {L"adj6", 2, 0, 4.629667, -0.2}, {L"adj7", 1, 0, 4.629632, -0.0}, {L"adj8", 0, 0, 4.629583, 0.2}}}},
			{55, {L"chevron", {{L"adj", 0, 8, -4.62963, 100000.0}}}},
			{58, {L"star8", {{L"adj", 0, 0, -4.62963, 50000.0}}}},
			{59, {L"star16", {{L"adj", 0, 0, -4.62963, 50000.0}}}},
			{61, {L"wedgeRectCallout", {{L"adj1", 0, 0, 4.629596, -49999.5}, {L"adj2", 1, 0, 4.62963, -50000.0}}}},
			{63, {L"wedgeEllipseCallout", {{L"adj1", 0, 0, 4.629596, -49999.5}, {L"adj2", 1, 0, 4.62963, -50000.0}}}},
			{64, {L"wave", {{L"adj1", 0, 0, 4.62963, 0.0}, {L"adj2", 1, 0, 4.62963, -50000.0}}}},
			{65, {L"foldedCorner", {{L"adj", 0, 0, -4.629585, 99999.3}}}},
			{66, {L"leftArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 1, 4.62963, 0.0}}}},
			{67, {L"downArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 9, -4.62963, 100000.0}}}},
			{68, {L"upArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 2, 4.62963, 0.0}}}},
			{69, {L"leftRightArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 1, 4.62963, 0.0}}}},
			{70, {L"upDownArrow", {{L"adj1", 0, 0, -9.259259, 100000.0}, {L"adj2", 1, 2, 4.62963, 0.0}}}},
			{71, {L"irregularSeal1", {}}},
			{72, {L"irregularSeal2", {}}},
			{77, {L"leftArrowCallout", {{L"adj1", 3, 9, -9.259259, 100000.0}, {L"adj2", 1, 9, -4.62963, 50000.0}, {L"adj3", 2, 1, 4.62963, 0.0}, {L"adj4", 0, 0, -4.629645, 100000.3}}}},
			{78, {L"rightArrowCallout", {{L"adj1", 3, 9, -9.259259, 100000.0}, {L"adj2", 1, 9, -4.62963, 50000.0}, {L"adj3", 2, 8, -4.62963, 100000.0}, {L"adj4", 0, 0, 4.629645, -0.1}}}},
			{79, {L"upArrowCallout", {{L"adj1", 3, 8, -9.259259, 100000.0}, {L"adj2", 1, 8, -4.62963, 50000.0}, {L"adj3", 2, 2, 4.62963, 0.0}, {L"adj4", 0, 0, -4.629645, 100000.3}}}},
			{80, {L"downArrowCallout", {{L"adj1", 3, 8, -9.259259, 100000.0}, {L"adj2", 1, 8, -4.62963, 50000.0}, {L"adj3", 2, 9, -4.62963, 100000.0}, {L"adj4", 0, 0, 4.629645, -0.1}}}},
			{81, {L"leftRightArrowCallout", {{L"adj1", 3, 9, -9.259259, 100000.0}, {L"adj2", 1, 9, -4.62963, 50000.0}, {L"adj3", 2, 1, 4.62963, 0.0}, {L"adj4", 0, 0, -9.260115, 100007.4}}}},
			{82, {L"upDownArrowCallout", {{L"adj1", 3, 8, -9.259259, 100000.0}, {L"adj2", 1, 8, -4.62963, 50000.0}, {L"adj3", 2, 2, 4.62963, 0.0}, {L"adj4", 0, 0, -9.260115, 100007.4}}}},
			{84, {L"bevel", {{L"adj", 0, 0, 4.62963, 0.0}}}},
			{85, {L"leftBracket", {{L"adj", 0, 2, 4.629689, -0.3}}}},
			{87, {L"leftBrace", {{L"adj1", 0, 2, 4.629704, -0.4}, {L"adj2", 1, 0, 4.62963, 0.0}}}},
			{88, {L"rightBrace", {{L"adj1", 0, 2, 4.629704, -0.4}, {L"adj2", 1, 0, 4.62963, 0.0}}}},
			{92, {L"star24", {{L"adj", 0, 0, -4.62963, 50000.0}}}},
			{93, {L"stripedRightArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 8, -4.62963, 100000.0}}}},
			{94, {L"notchedRightArrow", {{L"adj1", 1, 0, -9.259259, 100000.0}, {L"adj2", 0, 8, -4.62963, 100000.0}}}},
			{96, {L"smileyFace", {{L"adj", 0, 0, 4.629592, -76457.5}}}},
			{98, {L"horizontalScroll", {{L"adj", 0, 0, 4.62963, 0.0}}}},
			{106, {L"cloudCallout", {{L"adj1", 0, 0, 4.629596, -49999.5}, {L"adj2", 1, 0, 4.62963, -50000.0}}}},
			{109, {L"flowChartProcess", {}}},
			{110, {L"flowChartDecision", {}}},
			{111, {L"flowChartInputOutput", {}}},
			{112, {L"flowChartPredefinedProcess", {}}},
			{113, {L"flowChartInternalStorage", {}}},
			{114, {L"flowChartDocument", {}}},
			{115, {L"flowChartMultidocument", {}}},
			{116, {L"flowChartTerminator", {}}},
			{117, {L"flowChartPreparation", {}}},
			{118, {L"flowChartManualInput", {}}},
			{119, {L"flowChartManualOperation", {}}},
			{120, {L"flowChartConnector", {}}},
			{121, {L"flowChartPunchedCard", {}}},
			{122, {L"flowChartPunchedTape", {}}},
			{123, {L"flowChartSummingJunction", {}}},
			{124, {L"flowChartOr", {}}},
			{125, {L"flowChartCollate", {}}},
			{128, {L"flowChartMerge", {}}},
			{129, {L"flowChartOfflineStorage", {}}},
			{130, {L"flowChartOnlineStorage", {}}},
			{131, {L"flowChartMagneticTape", {}}},
			{132, {L"flowChartMagneticDisk", {}}},
			{133, {L"flowChartMagneticDrum", {}}},
			{134, {L"flowChartDisplay", {}}},
			{135, {L"flowChartDelay", {}}},
			{176, {L"flowChartAlternateProcess", {}}},
			{177, {L"flowChartOffpageConnector", {}}},
			{184, {L"moon", {{L"adj", 0, 0, 4.62963, 0.0}}}},
			{185, {L"bracketPair", {{L"adj", 0, 0, 4.629585, 0.3}}}},
			{186, {L"bracePair", {{L"adj", 0, 0, 4.629689, -0.3}}}},
			{187, {L"star4", {{L"adj", 0, 0, -4.62963, 50000.0}}}},
			{188, {L"doubleWave", {{L"adj1", 0, 0, 4.62963, 0.0}, {L"adj2", 1, 0, 4.62963, -50000.0}}}},
			{189, {L"actionButtonBlank", {}}},
			{190, {L"actionButtonHome", {}}},
			{191, {L"actionButtonHelp", {}}},
			{192, {L"actionButtonInformation", {}}},
			{193, {L"actionButtonForwardNext", {}}},
			{194, {L"actionButtonBackPrevious", {}}},
			{195, {L"actionButtonEnd", {}}},
			{197, {L"actionButtonReturn", {}}},
			{198, {L"actionButtonDocument", {}}},
			{200, {L"actionButtonMovie", {}}},
		};
		return presets;
	}

	// The a:prstGeom for a shape of legacy type spt (adj: its VML adj values; w, h: its size in any one unit), or ""
	inline std::wstring WordPresetGeometry(unsigned int spt, const std::vector<long>& adj, double w, double h)
	{
		std::map<unsigned int, WordPreset>::const_iterator it = WordPresets().find(spt);
		if (it == WordPresets().end())
			return L"";
		if (w <= 0 || h <= 0) w = h = 1;
		double ss = (std::min)(w, h);
		const double forms[] = {1, w / ss, h / ss, ss / w, ss / h, w / h, h / w};
		std::wstring av;
		for (const WordPresetGuide& g : it->second.guides)
		{
			if (g.adj >= (int)adj.size())
				continue;
			double x = g.adj < 0 ? 0 : adj[g.adj];
			long v = g.form >= 7 ? (long)std::lround((g.a * x + g.b) * forms[g.form - 7])
								 : (long)std::lround(g.a * x * forms[g.form] + g.b);
			av += L"<a:gd name=\"" + std::wstring(g.name) + L"\" fmla=\"val " + std::to_wstring(v) + L"\"/>";
		}
		return L"<a:prstGeom xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" prst=\""
			+ std::wstring(it->second.prst) + L"\"><a:avLst>" + av + L"</a:avLst></a:prstGeom>";
	}
}
