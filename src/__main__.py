import argparse
import os
from src.customFunction import (create_def_func_list,
                                create_cal_func_list,
                                LLmcustom)
import json


def parser_data() -> argparse.Namespace:
    "checks for flags returns default if no flags were used"
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--functions_definition",
                        default="data/input/functions_definition.json",
                        help="custom input for path of "
                        "function_definition.json")
    parser.add_argument("--input",
                        default="data/input/function_calling_tests.json",
                        help="custom input for path of "
                        "function_calling.json")
    parser.add_argument("--output",
                        default="data/output/function_calls.json",
                        help="custom output for path")
    return parser.parse_args()


def main() -> None:
    "runs the whole programm"
    output = []
    try:
        parser = parser_data()
        cal_func = create_cal_func_list(parser.input)
        def_func = create_def_func_list(parser.functions_definition)
    except Exception as e:
        print(e)
        exit()
    model = LLmcustom(func_def=def_func)
    for x in cal_func:
        res = model.get_ouput(x)
        output.append(res)

    print(f"exporting output to: {parser.output}")
    try:
        os.makedirs(os.path.dirname(parser.output), exist_ok=True)
        with open(parser.output, "w") as f:
            json.dump([x.model_dump(mode="json") for x in output], f, indent=4)
    except Exception as e:
        print(e)
        exit()


if __name__ == "__main__":
    main()
