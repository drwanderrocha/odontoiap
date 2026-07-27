#!/usr/bin/env python3
"""
Populate Cognee memory with biomechanical rules from the teach workspace.
Run this after setting up Cognee (local or cloud) and configuring LLM_API_KEY.
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_cognee import ClinicalMemory, MemoryConfig


BIOMECHANICAL_RULES = [
    # From Lição 01 - M/F Ratio Fundamentals
    {
        "movement_type": "bodily_translation",
        "tooth_type": "incisor_central_superior",
        "mf_ratio_mm": 11.0,
        "attachment_design": {
            "shape": "rectangular",
            "position": "middle_third_vestibular",
            "dimensions_mm": {"width": 3.0, "height": 2.0, "depth": 1.5}
        },
        "overcorrection_factor": 1.1,
        "source": "Nanda & Tosun 2020, Kwon 2020, Simon 2018",
        "confidence": 0.9
    },
    {
        "movement_type": "bodily_translation",
        "tooth_type": "canine_superior",
        "mf_ratio_mm": 9.0,
        "attachment_design": {
            "shape": "rectangular",
            "position": "middle_third_vestibular",
            "dimensions_mm": {"width": 3.5, "height": 2.5, "depth": 1.5}
        },
        "overcorrection_factor": 1.1,
        "source": "Nanda & Tosun 2020, Kwon 2020",
        "confidence": 0.85
    },
    {
        "movement_type": "bodily_translation",
        "tooth_type": "premolar_superior",
        "mf_ratio_mm": 7.0,
        "attachment_design": {
            "shape": "rectangular",
            "position": "middle_third_vestibular",
            "dimensions_mm": {"width": 3.0, "height": 2.0, "depth": 1.5}
        },
        "overcorrection_factor": 1.1,
        "source": "Nanda & Tosun 2020",
        "confidence": 0.85
    },
    {
        "movement_type": "bodily_translation",
        "tooth_type": "molar_superior",
        "mf_ratio_mm": 5.0,
        "attachment_design": {
            "shape": "ellipsoid",
            "position": "vestibular_buccal_gingival",
            "dimensions_mm": {"width": 4.0, "height": 3.0, "depth": 1.5}
        },
        "overcorrection_factor": 1.1,
        "source": "Kwon 2020, Gong 2022 (FEA)",
        "confidence": 0.8
    },
    {
        "movement_type": "labial_torque",
        "tooth_type": "incisor_central_superior",
        "mf_ratio_mm": 15.0,
        "attachment_design": {
            "shape": "power_ridge_or_dual_attachment",
            "position": "gingival_power_ridge + incisal_attachment",
            "dimensions_mm": {"power_ridge_height": 1.5, "attachment_width": 3.0}
        },
        "overcorrection_factor": 1.3,
        "source": "Simon 2018 (optimized attachments), Kwon 2020",
        "confidence": 0.85
    },
    {
        "movement_type": "lingual_torque",
        "tooth_type": "incisor_central_superior",
        "mf_ratio_mm": 15.0,
        "attachment_design": {
            "shape": "power_ridge_or_dual_attachment",
            "position": "incisal_power_ridge + gingival_attachment",
            "dimensions_mm": {"power_ridge_height": 1.5, "attachment_width": 3.0}
        },
        "overcorrection_factor": 1.3,
        "source": "Simon 2018, Kwon 2020",
        "confidence": 0.85
    },
    {
        "movement_type": "intrusion",
        "tooth_type": "incisor_superior",
        "mf_ratio_mm": 0.0,
        "attachment_design": {
            "shape": "horizontal_rectangular_anchorage",
            "position": "vestibular_on_adjacent_teeth_for_anchorage",
            "dimensions_mm": {"width": 4.0, "height": 2.0, "depth": 1.5}
        },
        "overcorrection_factor": 1.2,
        "source": "Rossini 2015, Kwon 2020",
        "confidence": 0.8
    },
    {
        "movement_type": "rotation",
        "tooth_type": "canine_superior",
        "mf_ratio_mm": 0.0,
        "attachment_design": {
            "shape": "ellipsoid_or_beveled",
            "position": "mesial_vestibular_for_distal_rotation",
            "dimensions_mm": {"width": 3.5, "height": 3.0, "depth": 1.5, "bevel_angle": 45}
        },
        "overcorrection_factor": 1.75,
        "source": "Simon 2018 (optimized rotation attachments), Kwon 2020",
        "confidence": 0.9
    },
    {
        "movement_type": "extrusion",
        "tooth_type": "incisor_superior",
        "mf_ratio_mm": 3.0,
        "attachment_design": {
            "shape": "horizontal_rectangular",
            "position": "incisal_vestibular_for_elastic_hook",
            "dimensions_mm": {"width": 3.0, "height": 2.0, "depth": 1.5}
        },
        "overcorrection_factor": 1.2,
        "source": "Kwon 2020 (aligner alone poor for extrusion)",
        "confidence": 0.75
    },
    {
        "movement_type": "mesial_distal_bodily",
        "tooth_type": "molar_superior",
        "mf_ratio_mm": 5.0,
        "attachment_design": {
            "shape": "rectangular_buccal_palatal_pair",
            "position": "buccal_middle + palatal_middle",
            "dimensions_mm": {"width": 4.0, "height": 3.0, "depth": 1.5}
        },
        "overcorrection_factor": 1.1,
        "source": "Kwon 2020, Gong 2022",
        "confidence": 0.8
    }
]


async def populate_biomechanics():
    """Populate Cognee with biomechanical rules."""
    config = MemoryConfig(
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        cognee_base_url=os.getenv("COGNEE_BASE_URL"),
        cognee_api_key=os.getenv("COGNEE_API_KEY"),
        postgres_dsn=os.getenv("DATABASE_URL"),
        dataset="odontoai_clinical"
    )
    
    if not config.llm_api_key:
        print("❌ LLM_API_KEY not set. Set it in environment or .env")
        return
    
    memory = ClinicalMemory(config)
    await memory.initialize()
    
    print(f"📚 Populating {len(BIOMECHANICAL_RULES)} biomechanical rules...")
    
    for i, rule in enumerate(BIOMECHANICAL_RULES, 1):
        try:
            rule_id = await memory.store_biomechanical_rule(
                movement_type=rule["movement_type"],
                tooth_type=rule["tooth_type"],
                mf_ratio_mm=rule["mf_ratio_mm"],
                attachment_design=rule["attachment_design"],
                overcorrection_factor=rule["overcorrection_factor"],
                source=rule["source"],
                confidence=rule["confidence"]
            )
            print(f"  ✅ [{i}/{len(BIOMECHANICAL_RULES)}] {rule_id}")
        except Exception as e:
            print(f"  ❌ [{i}] Failed: {e}")
    
    # Verify retrieval
    print("\n🔍 Testing retrieval...")
    results = await memory.get_biomechanical_rules(movement_type="bodily_translation")
    print(f"   Found {len(results)} rules for bodily_translation")
    for r in results[:3]:
        meta = r.get("metadata", {})
        print(f"   - {meta.get('movement')} / {meta.get('tooth')}: M/F={meta.get('mf_ratio_mm')}mm")
    
    await memory.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(populate_biomechanics())