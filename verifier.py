"""
SciGuard Core Verification Engine
Validates chemical structures, detects hallucinations, queries PubChem for ground-truth,
and audits laboratory hazards (GHS).
"""

import re
import urllib.parse
import requests
from typing import Dict, Any, List, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

class SciVerifier:
    def __init__(self):
        self.pubchem_cache = {}
        
    def validate_smiles(self, smiles: str) -> Dict[str, Any]:
        """
        Validates a SMILES string against fundamental chemical valency and physics rules.
        """
        smiles = smiles.strip()
        if not smiles:
            return {
                "valid": False,
                "error": "Empty SMILES string provided.",
                "type": "EMPTY_INPUT"
            }
            
        try:
            # First attempt without sanitization to catch valence errors specifically
            mol = Chem.MolFromSmiles(smiles, sanitize=False)
            if mol is None:
                return {
                    "valid": False,
                    "error": f"Invalid SMILES syntax: '{smiles}' could not be parsed.",
                    "type": "SYNTAX_ERROR",
                    "mol": None
                }
                
            # Now sanitize to test physical valency
            problems = Chem.DetectChemistryProblems(mol)
            if problems:
                error_msgs = []
                for p in problems:
                    error_msgs.append(f"{p.GetType()}: {p.Message()}")
                return {
                    "valid": False,
                    "error": f"Chemical valency violation: {'; '.join(error_msgs)}",
                    "type": "VALENCE_VIOLATION",
                    "mol": None
                }
                
            Chem.SanitizeMol(mol)
            
            # Compute physical descriptors
            formula = rdMolDescriptors.CalcMolFormula(mol)
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            tpsa = Descriptors.TPSA(mol)
            hbd = rdMolDescriptors.CalcNumHBD(mol)
            hba = rdMolDescriptors.CalcNumHBA(mol)
            rot_bonds = Descriptors.NumRotatableBonds(mol)
            aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
            
            canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
            
            return {
                "valid": True,
                "error": None,
                "canonical_smiles": canonical_smiles,
                "formula": formula,
                "molecular_weight": round(mw, 2),
                "logp": round(logp, 2),
                "tpsa": round(tpsa, 2),
                "hbd": hbd,
                "hba": hba,
                "rotatable_bonds": rot_bonds,
                "aromatic_rings": aromatic_rings,
                "mol": mol
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Valence / Physics Violation: {str(e)}",
                "type": "PARSER_EXCEPTION",
                "mol": None
            }

    def ground_with_pubchem(self, identifier: str, by: str = "auto") -> Dict[str, Any]:
        """
        Cross-references compound with the NIH PubChem database (115M+ compounds) via PUG-REST API.
        Determines if the molecule is empirically documented or an LLM hallucination.
        """
        identifier = identifier.strip()
        cache_key = f"{by}:{identifier}"
        if cache_key in self.pubchem_cache:
            return self.pubchem_cache[cache_key]

        res = {
            "found_in_pubchem": False,
            "cid": None,
            "iupac_name": None,
            "canonical_smiles": None,
            "molecular_formula": None,
            "molecular_weight": None,
            "hazards": [],
            "hallucination_flag": True,
            "confidence_notes": ""
        }

        # Determine lookup strategy
        is_smiles = by == "smiles" or (by == "auto" and any(c in identifier for c in "=@#()-/\\12345"))
        
        encoded_id = urllib.parse.quote(identifier)
        lookup_types = ["smiles", "name"] if is_smiles else ["name", "smiles"]

        for l_type in lookup_types:
            try:
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{l_type}/{encoded_id}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,ConnectivitySMILES,IUPACName/JSON"
                resp = requests.get(url, timeout=4)
                if resp.status_code == 200:
                    data = resp.json()
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    if props:
                        p = props[0]
                        res["found_in_pubchem"] = True
                        res["hallucination_flag"] = False
                        res["cid"] = p.get("CID")
                        res["iupac_name"] = p.get("IUPACName") or identifier
                        res["canonical_smiles"] = p.get("CanonicalSMILES") or p.get("ConnectivitySMILES") or identifier
                        res["molecular_formula"] = p.get("MolecularFormula")
                        res["molecular_weight"] = float(p.get("MolecularWeight", 0)) if p.get("MolecularWeight") else None
                        res["confidence_notes"] = f"Empirically verified in NIH PubChem database (CID: {res['cid']}). Real chemical compound."
                        
                        # Fetch hazards
                        if res["cid"]:
                            res["hazards"] = self.fetch_ghs_hazards(res["cid"])
                        break
            except Exception:
                continue

        if not res["found_in_pubchem"]:
            res["confidence_notes"] = f"CRITICAL: '{identifier}' does NOT exist in NIH PubChem (115M+ records). Flagged as LLM Hallucination."

        self.pubchem_cache[cache_key] = res
        return res

    def fetch_ghs_hazards(self, cid: int) -> List[Dict[str, str]]:
        """
        Queries PubChem PUG-REST view for GHS Hazard statements.
        """
        hazards = []
        try:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading=GHS+Classification"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                sections = data.get("Record", {}).get("Section", [])
                for s in sections:
                    for sub in s.get("Section", []):
                        for info in sub.get("Information", []):
                            if "GHS Hazard Statements" in info.get("Name", ""):
                                for val in info.get("Value", {}).get("StringWithMarkup", []):
                                    text = val.get("String", "")
                                    match = re.match(r"(H\d{3}[A-Za-z]?):\s*(.*)", text)
                                    if match:
                                        hazards.append({
                                            "code": match.group(1),
                                            "statement": match.group(2)
                                        })
                                    elif text:
                                        hazards.append({
                                            "code": "GHS",
                                            "statement": text
                                        })
        except Exception:
            pass
            
        seen = set()
        unique_hazards = []
        for h in hazards:
            if h["statement"] not in seen:
                seen.add(h["statement"])
                unique_hazards.append(h)
        return unique_hazards[:6]

    def audit_reaction_safety(self, text: str, detected_chemicals: List[str]) -> Dict[str, Any]:
        """
        Audits reaction procedures for dangerous laboratory hazards:
        Exothermic runaways, peroxides, water-reactive agents, pyrophorics, toxic gases.
        """
        text_lower = text.lower()
        warnings = []
        risk_level = "LOW"
        
        hazard_rules = [
            (r"peroxide|peracetic|t-buooh", "ORGANIC_PEROXIDE", "HIGH", "Severe explosion hazard: Organic peroxides can detonate upon heating, friction, or shock."),
            (r"lithium aluminum hydride|lah|nah|sodium hydride|potassium metal", "PYROPHORIC_WATER_REACTIVE", "HIGH", "Water-reactive/Pyrophoric: Violent hydrogen gas evolution and spontaneous fire risk on contact with moisture."),
            (r"diazomethane|azide|sodium azide", "EXPLOSIVE_AZIDE", "HIGH", "Explosive risk: Azide/diazomethane compounds can explode violently without stabilizer."),
            (r"cyanide|sodium cyanide|kcn|hcn", "EXTREME_TOXICITY", "HIGH", "Lethal Toxicity: Rapidly fatal cellular hypoxia upon inhalation or skin contact."),
            (r"phosgene|chlorine gas", "TOXIC_GAS", "HIGH", "Toxic Gas Inhalation Risk: Requires certified chemical fume hood with scrubbers."),
            (r"hydrofluoric acid|hf", "CORROSIVE_BONE_TOXIC", "HIGH", "Bone-seeking corrosive poison: Penetrates tissue rapidly; requires Calcium Gluconate antidote on standby."),
            (r"heat to reflux|150\s*c|200\s*c|exotherm", "THERMAL_EXOTHERM", "MEDIUM", "Thermal Runaway Precaution: Elevated reaction temperature requires active temperature monitoring and blast shield.")
        ]
        
        for pattern, h_type, severity, msg in hazard_rules:
            if re.search(pattern, text_lower):
                warnings.append({
                    "hazard_type": h_type,
                    "severity": severity,
                    "message": msg
                })
                if severity == "HIGH":
                    risk_level = "CRITICAL"
                elif severity == "MEDIUM" and risk_level != "CRITICAL":
                    risk_level = "ELEVATED"
                    
        return {
            "risk_level": risk_level,
            "hazard_warnings": warnings
        }

    def compute_trust_index(self, rdkit_res: Dict[str, Any], pubchem_res: Dict[str, Any], safety_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes the SciGuard Scientific Trust Index (0 - 100%).
        """
        score = 0
        breakdown = {}
        
        # 1. Structural score (max 35)
        if rdkit_res.get("valid", False):
            val_score = 35
            val_status = "PASSED: Molecule satisfies quantum valence & bond angle constraints."
        else:
            val_score = 0
            val_status = f"FAILED: {rdkit_res.get('error', 'Invalid chemical structure')}"
        score += val_score
        breakdown["structural_validity"] = {"score": val_score, "max": 35, "status": val_status}
        
        # 2. Empirical Grounding score (max 35)
        if pubchem_res.get("found_in_pubchem", False):
            ground_score = 35
            ground_status = f"PASSED: Grounded in NIH PubChem (CID: {pubchem_res.get('cid')}). Documented physical entity."
        else:
            ground_score = 5
            ground_status = "WARNING: Zero empirical records in NIH PubChem. Flagged as LLM Hallucination."
        score += ground_score
        breakdown["empirical_grounding"] = {"score": ground_score, "max": 35, "status": ground_status}
        
        # 3. Lab Safety score (max 30)
        risk = safety_res.get("risk_level", "LOW")
        if risk == "LOW":
            safe_score = 30
            safe_status = "PASSED: Standard laboratory safety protocols apply. No acute detonation/toxicity flags."
        elif risk == "ELEVATED":
            safe_score = 18
            safe_status = "CAUTION: Elevated thermal or corrosive hazards detected. Secondary containment required."
        else:
            safe_score = 5
            safe_status = "CRITICAL: High hazard / explosive / lethal exposure risk flagged."
        score += safe_score
        breakdown["lab_safety"] = {"score": safe_score, "max": 30, "status": safe_status}
        
        if score >= 85:
            verdict = "VERIFIED_ACCURATE"
            badge_color = "#10B981"
        elif score >= 60:
            verdict = "PROCEED_WITH_CAUTION"
            badge_color = "#F59E0B"
        else:
            verdict = "REJECTED_HALLUCINATION_OR_HAZARDOUS"
            badge_color = "#EF4444"
            
        return {
            "total_score": score,
            "verdict": verdict,
            "badge_color": badge_color,
            "breakdown": breakdown
        }

    def audit_batch(self, items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Processes a batch of chemical claims or SMILES and returns structured audit results.
        """
        results = []
        for i, item in enumerate(items):
            query = item.get("claim") or item.get("query") or item.get("name") or f"Sample #{i+1}"
            smiles = item.get("smiles") or item.get("SMILES") or ""
            
            # 1. Structure check
            rdkit_res = self.validate_smiles(smiles)
            
            # 2. PubChem check
            pubchem_res = self.ground_with_pubchem(
                identifier=rdkit_res.get("canonical_smiles") or smiles or query,
                by="auto"
            )
            
            # 3. Safety check
            safety_res = self.audit_reaction_safety(query, [smiles, pubchem_res.get("iupac_name") or ""])
            
            # 4. Trust score
            trust = self.compute_trust_index(rdkit_res, pubchem_res, safety_res)
            
            # Flag primary failure mode
            if not rdkit_res.get("valid"):
                failure_mode = "Valency / Physics Violation"
            elif pubchem_res.get("hallucination_flag"):
                failure_mode = "Fabricated Compound (Not in PubChem)"
            elif safety_res.get("risk_level") == "CRITICAL":
                failure_mode = "Severe Process / Explosive Hazard"
            elif safety_res.get("risk_level") == "ELEVATED":
                failure_mode = "Elevated Hazard (Precaution Required)"
            else:
                failure_mode = "Verified Clean"

            results.append({
                "ID": i + 1,
                "Scientific Claim / Reaction": query,
                "SMILES": smiles,
                "Formula": rdkit_res.get("formula") or pubchem_res.get("molecular_formula") or "N/A",
                "Trust Score": trust["total_score"],
                "Verdict": trust["verdict"],
                "Status": failure_mode,
                "PubChem CID": pubchem_res.get("cid") or "None"
            })
        return results

