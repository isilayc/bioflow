from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load(name):
    with (DATA/name).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    tools=load("tools.yaml")
    tool_io=load("tool_io.yaml")
    workflows=load("workflows.yaml")
    constraints=load("constraints.yaml")
    strategy=load("strategy_fit.yaml")

    for tid in ("catbat","sourmash"):
        if tid not in tools:
            fail(f"{tid} missing from tools.yaml")
        if "mag_taxonomy" not in (tools[tid].get("operations") or []):
            fail(f"{tid} does not declare mag_taxonomy")
        routes=tool_io.get(tid,{}).get("routes",[]) or []
        if not any(r.get("requires")==["mag_bins"] and r.get("produces")==["genome_taxonomy"] for r in routes):
            fail(f"{tid} missing mag_bins -> genome_taxonomy route")
        if tid not in constraints.get("tools",{}):
            fail(f"{tid} constraint definition missing")

    mag_workflows=[]
    for wid,wf in workflows.items():
        for step in wf.get("steps",[]) or []:
            if step.get("operation")=="mag_taxonomy":
                mag_workflows.append(wid)
                c=step.get("candidates",[]) or []
                for tid in ("gtdbtk","catbat","sourmash"):
                    if tid not in c:
                        fail(f"{wid} mag_taxonomy missing candidate {tid}")
                op=(strategy.get("workflows",{}).get(wid,{})
                    .get("operations",{}).get("mag_taxonomy",{}))
                if op.get("gtdbtk",{}).get("fit") != "strong":
                    fail(f"{wid}: GTDB-Tk should remain strong fit")
                if op.get("catbat",{}).get("fit") != "supported":
                    fail(f"{wid}: CAT/BAT should be supported fit")
                if op.get("sourmash",{}).get("fit") != "supported":
                    fail(f"{wid}: sourmash should be supported fit")

    if not mag_workflows:
        fail("No mag_taxonomy workflows found")

    sys.path.insert(0, str(ROOT))
    from engine.constraints import evaluate_tool_constraints
    from engine.scoring import recommendation_sort_key

    g_block=evaluate_tool_constraints("gtdbtk", {
        "gtdbtk_database_compatible": False,
        "gtdbtk_input_is_bacteria_archaea": True,
        "gtdbtk_genomes_quality_screened": True,
    })
    cat_pass=evaluate_tool_constraints("catbat", {
        "gtdbtk_input_is_bacteria_archaea": True,
        "catbat_database_available": True,
    })
    sm_pass=evaluate_tool_constraints("sourmash", {
        "gtdbtk_input_is_bacteria_archaea": True,
        "sourmash_reference_database_available": True,
        "sourmash_taxonomy_mapping_available": True,
    })
    if g_block.get("status") != "block": fail("GTDB-Tk synthetic database failure did not BLOCK")
    if cat_pass.get("status") != "pass": fail("CAT/BAT synthetic available-db case did not PASS")
    if sm_pass.get("status") != "pass": fail("sourmash synthetic available-db case did not PASS")

    cat_domain_block=evaluate_tool_constraints("catbat", {
        "gtdbtk_input_is_bacteria_archaea": False,
        "catbat_database_available": True,
    })
    sm_domain_block=evaluate_tool_constraints("sourmash", {
        "gtdbtk_input_is_bacteria_archaea": False,
        "sourmash_reference_database_available": True,
        "sourmash_taxonomy_mapping_available": True,
    })
    if cat_domain_block.get("status") != "block": fail("CAT/BAT must not bypass MAG domain-scope mismatch")
    if sm_domain_block.get("status") != "block": fail("sourmash must not bypass MAG domain-scope mismatch")

    # Explicitly test the ranking-v3 hard-gate behavior.
    gtool={"score":{"scientific_fit_label":"strong","scientific_fit_priority":4,"total":100}}
    ctool={"score":{"scientific_fit_label":"supported","scientific_fit_priority":3,"total":80}}
    if recommendation_sort_key(ctool,constraint_status="pass") <= recommendation_sort_key(gtool,constraint_status="block"):
        fail("A passing fallback does not outrank BLOCKed GTDB-Tk")
    if recommendation_sort_key(gtool,constraint_status="pass") <= recommendation_sort_key(ctool,constraint_status="pass"):
        fail("Passing GTDB-Tk should remain preferred over passing supported fallback")

    print("MAG taxonomy workflows:", ", ".join(sorted(set(mag_workflows))))
    print("GTDB-Tk database unavailable -> BLOCK: PASS")
    print("CAT/BAT database available -> PASS: PASS")
    print("sourmash database+taxonomy available -> PASS: PASS")
    print("Non-bacterial/non-archaeal domain mismatch blocks curated MAG fallbacks: PASS")
    print("Ranking hard-gate fallback behavior: PASS")
    print("RESULT: PASS")

if __name__ == "__main__":
    main()
