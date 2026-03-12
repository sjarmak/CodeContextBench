import json, sys, re
sys.path.insert(0, "/tests")
from verifiers import SemanticRetrievalQAVerifier

try:
    with open("/tests/ground_truth.json") as f:
        ground_truth = json.load(f)
    with open("/app/solution.json") as f:
        raw = f.read()
    matches = re.findall(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL)
    if matches:
        raw = matches[-1].strip()
    agent_output = json.loads(raw)

    verifier = SemanticRetrievalQAVerifier(ground_truth)
    result = verifier.verify(agent_output)
    reward = {"score": float(result.correct_function)}

    print(f"Correct Function: {result.correct_function:.2f}")
    print(f"Correct Path: {result.correct_path:.2f}")
    print(f"Justification: {result.justification_score:.2f}")
    print(f"Details: {result.reasoning}")

    with open("/logs/verifier/reward.json", "w") as f:
        json.dump(reward, f, indent=2)
    with open("/logs/verifier/reward.txt", "w") as f:
        f.write(str(reward["score"]))
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    with open("/logs/verifier/reward.json", "w") as f:
        json.dump({"score": 0.0}, f)
    with open("/logs/verifier/reward.txt", "w") as f:
        f.write("0.0")
