import json
import httpx
import sys
import argparse
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    # Load public samples
    try:
        with open("BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json", "r") as f:
            data = json.load(f)
            cases = data.get("cases", data)
    except FileNotFoundError:
        print("Error: Could not find BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json")
        sys.exit(1)

    print(f"Running {len(cases)} public sample cases against {args.base_url}", flush=True)
    
    passed = 0
    failed = 0

    with httpx.Client(timeout=60) as client:
        for case in cases:
            time.sleep(5)
            scenario_id = case["input"]["scenario_id"]
            print(f"Running {scenario_id}...", flush=True)
            
            try:
                response = client.post(f"{args.base_url}/optimize-energy", json=case["input"])
                
                if response.status_code != 200:
                    print(f"  FAIL: HTTP {response.status_code}")
                    print(f"  Response: {response.text}")
                    failed += 1
                    continue
                    
                data = response.json()
                
                # Check interpretations semantically
                expected_interps = case["expected_output"]["directive_interpretation"]
                actual_interps = data["directive_interpretation"]
                
                if len(expected_interps) != len(actual_interps):
                    print(f"  FAIL: Interpretation length mismatch. Expected {len(expected_interps)}, got {len(actual_interps)}")
                    failed += 1
                    continue
                
                interp_failed = False
                for exp, act in zip(expected_interps, actual_interps):
                    if exp["applies"] != act["applies"] or exp["directive_type"] != act["directive_type"]:
                        print(f"  FAIL: Interpretation mismatch.")
                        print(f"    Expected: {exp['applies']} / {exp['directive_type']}")
                        print(f"    Actual:   {act['applies']} / {act['directive_type']}")
                        interp_failed = True
                        break
                    
                    if exp["applies"]:
                        # compare structural adjustments
                        if exp["structured_adjustment"] != act["structured_adjustment"]:
                            print(f"  FAIL: Structural adjustment mismatch.")
                            print(f"    Expected: {exp['structured_adjustment']}")
                            print(f"    Actual:   {act['structured_adjustment']}")
                            interp_failed = True
                            break
                if interp_failed:
                    failed += 1
                    continue
                
                # Check cost tolerance
                expected_cost = case["expected_output"]["total_cost_bdt"]
                actual_cost = data["total_cost_bdt"]
                
                if abs(expected_cost - actual_cost) > 0.01:
                    print(f"  FAIL: Cost mismatch. Expected {expected_cost}, got {actual_cost}")
                    failed += 1
                    continue
                
                print(f"  PASS", flush=True)
                passed += 1

            except Exception as e:
                print(f"  FAIL: Request error: {e}", flush=True)
                failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed.", flush=True)
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
