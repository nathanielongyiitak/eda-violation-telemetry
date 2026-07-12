import sys
import re

err_name = re.compile(r"(.+\..+\(.+)")
err_val = re.compile(r".+: (.+)")

def parse_eda_stream(file_path):
    current_stage = None
    vertices_remaining = 0
    current_violation = {}
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                
                # FIX 3: Check for a new error FIRST, completely unguarded
                name_match = err_name.search(line)
                if name_match:
                    if current_violation:
                        yield current_violation
                    current_violation = {"err_name": name_match.group(1)}
                    current_stage = "err_start"
                    continue
                
                # Process states if we are inside an active error block
                if current_stage in ["err_start", "total_saved", "layer_saved", "type_saved"]:
                    val_match = err_val.search(line) # FIX 1: Safe assignment
                    if val_match:
                        val_str = val_match.group(1)
                        if "TOTAL" in line:
                            current_violation["total"] = val_str
                            current_stage = "total_saved"
                        elif "Layer:" in line:
                            current_violation["err_lay"] = val_str
                            current_stage = "layer_saved"
                        elif "Type:" in line:
                            current_violation["err_type"] = val_str
                            current_stage = "type_saved"
                        elif "Vertices" in line:
                            vertices_remaining = int(val_str) # FIX 2: Pythonic cast
                            current_violation.setdefault("err_vertices", []).append(vertices_remaining)
                            current_stage = "vertices_saved"
                        continue
                
                elif current_stage == "coords_saved":
                    val_match = err_val.search(line)
                    if val_match:
                        vertices_remaining = int(val_match.group(1))
                        current_violation.setdefault("err_vertices", []).append(vertices_remaining)
                        current_stage = "vertices_saved"
                        continue
                    # Note: We do NOT yield here anymore. The top 'name_match' handles the yielding!
                
                elif current_stage == "vertices_saved":
                    current_violation.setdefault("err_coords", []).append(line)
                    vertices_remaining -= 1
                    if vertices_remaining == 0:
                        current_stage = "coords_saved"
                        continue

            if current_violation:
                yield current_violation
                
    except Exception as e:
        print(f"Stream interrupted: {e} on line: {line}", file=sys.stderr)
        current_stage = None

def main():
    # Test this with your sample.log file
    for obj in parse_eda_stream("./sample.log"):
        print(obj)

if __name__ == "__main__":
    main()