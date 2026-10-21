"""
SciGuard Molecular Visualizer
Generates interactive 3D WebGL molecular viewers and crisp 2D structure diagrams.
"""

import urllib.parse
import requests
from rdkit import Chem
from rdkit.Chem import Draw

def get_3d_sdf_from_pubchem(cid: int) -> str:
    """
    Fetches real experimental/calculated 3D conformer SDF from NIH PubChem.
    """
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/SDF/?record_type=3d"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200 and "$$$$" in resp.text:
            return resp.text
    except Exception:
        pass
    
    # Fallback to 2D SDF if 3D conformer not computed
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/SDF/?record_type=2d"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
        
    return ""

def generate_3d_html(sdf_data: str, mol_title: str = "Molecule", style: str = "stick", auto_rotate: bool = True) -> str:
    """
    Builds a standalone interactive WebGL 3Dmol.js viewer.
    Allows orbiting, panning, zooming, and inspecting atom coordinates.
    """
    if not sdf_data:
        return """
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 12px; padding: 40px; text-align: center; color: #94a3b8; font-family: sans-serif;">
            <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="margin-bottom: 12px;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <p style="margin: 0; font-weight: 500;">No 3D conformer data available for this structure.</p>
        </div>
        """
        
    # Escape SDF for JavaScript template literal
    clean_sdf = sdf_data.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    
    style_json = ""
    if style == "stick":
        style_json = "{stick: {radius: 0.15, colorscheme: 'Jmol'}}"
    elif style == "sphere":
        style_json = "{sphere: {scale: 0.3, colorscheme: 'Jmol'}, stick: {radius: 0.1, colorscheme: 'Jmol'}}"
    elif style == "spacefill":
        style_json = "{sphere: {colorscheme: 'Jmol'}}"
    else:
        style_json = "{stick: {colorscheme: 'Jmol'}}"

    spin_script = "viewer.spin('y', 0.8);" if auto_rotate else ""

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
        <style>
            body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: transparent; font-family: system-ui, -apple-system, sans-serif; }}
            #viewport {{ width: 100%; height: 420px; position: relative; border-radius: 12px; overflow: hidden; background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%); border: 1px solid rgba(255,255,255,0.1); box-shadow: inset 0 2px 8px rgba(0,0,0,0.4); }}
            .overlay-badge {{ position: absolute; top: 14px; left: 16px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); z-index: 10; pointer-events: none; }}
            .controls-hint {{ position: absolute; bottom: 12px; right: 14px; background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px); padding: 4px 10px; border-radius: 6px; font-size: 11px; color: #94a3b8; border: 1px solid rgba(255,255,255,0.05); z-index: 10; pointer-events: none; }}
        </style>
    </head>
    <body>
        <div id="viewport">
            <div class="overlay-badge">🌐 3D Interactive Conformer: {mol_title}</div>
            <div class="controls-hint">🖱️ Left-Click: Orbit &middot; Right-Click: Pan &middot; Scroll: Zoom</div>
        </div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                let element = document.getElementById('viewport');
                let config = {{ backgroundColor: 'transparent' }};
                let viewer = $3Dmol.createViewer(element, config);
                let sdfData = `{clean_sdf}`;
                
                viewer.addModel(sdfData, "sdf");
                viewer.setStyle({{}}, {style_json});
                viewer.zoomTo();
                viewer.render();
                {spin_script}
                
                element.addEventListener('mousedown', function() {{
                    viewer.spin(false);
                }});
            }});
        </script>
    </body>
    </html>
    """
    return html_code

def get_2d_mol_svg(mol_or_smiles) -> str:
    """
    Generates high-definition 2D chemical structure SVG.
    """
    try:
        if isinstance(mol_or_smiles, str):
            mol = Chem.MolFromSmiles(mol_or_smiles)
        else:
            mol = mol_or_smiles
            
        if mol is None:
            return ""
            
        d2d = Draw.MolDraw2DSVG(360, 260)
        opts = d2d.drawOptions()
        opts.clearBackground = False
        d2d.DrawMolecule(mol)
        d2d.FinishDrawing()
        return d2d.GetDrawingText()
    except Exception:
        return ""
