*This project has been created as part of the 42 curriculum by tkroon*

<!--
DRAFT NOTES (delete before submitting):
- Everything marked TODO is something only you can fill in or verify.
- Every claim below must be true of YOUR final code. Reread each section
  against the code before submitting, and be ready to explain it aloud.
- The README must be in English (subject, chapter VI).
-->

# call me maybe

imports a list of promts and functions and convert them to the correct function to  use.

## Description

**Goal.** Translate a natural-language request into a structured function call.
Given `"What is the sum of 40 and 2?"`, the program does not answer `42`. It
returns the function to call and its typed arguments:

```json
{
    "prompt": "What is the sum of 40 and 2?",
    "name": "fn_add_numbers",
    "parameters": {"a": 40.0, "b": 2.0}
}
```

**Overview.** The program reads a list of available functions
(`functions_definition.json`) and a list of prompts
(`function_calling_tests.json`). For each prompt, the small language model
`Qwen/Qwen3-0.6B` (through the provided `llm_sdk` wrapper) chooses the function
and the parameter values. The results are written to a JSON file.

Instead of letting the model write free text and hoping it is usable, the
program steers generation token by token: it reads the model's logits at each
step and sets the logits of tokens that are not allowed to `-inf` before picking
the next token.

## Instructions

**Requirements:** Python 3.10 or later, [uv](https://docs.astral.sh/uv/).

```bash
make install     # uv sync: creates the virtual environment, installs dependencies
make run         # runs the program with the default paths
make debug       # runs the program under pdb
make lint        # flake8 + mypy with the flags required by the subject
make lint-strict # flake8 + mypy --strict (optional)
make clean       # removes __pycache__ and .mypy_cache
```
Run it directly:

```bash
uv run python -m src \
    --functions_definition data/input/functions_definition.json \
    --input data/input/function_calling_tests.json \
    --output data/output/function_calls.json
```

| Flag | Default |
| --- | --- |
| `--functions_definition` | `data/input/functions_definition.json` |
| `--input` | `data/input/function_calling_tests.json` |
| `--output` | `data/output/function_calls.json` |

## Algorithm explanation

### 1. Loading and validating input

`json_convert.py` loads both input files and validates them with pydantic
(`DefinedFunction`, `CallingFunction`). Missing files, invalid JSON, wrong
types and missing keys raise errors with a readable message.

### 2. Choosing the function

1. A prompt is built from the user request and the list of functions (name and
   description).
2. The prompt is encoded and the model returns the logits for the next token.
3. The highest-scoring token is tested: the decoded text so far must still be a
   prefix of at least one defined function name. If not, its logit is set to
   `-inf` and the next best token is tried.
4. Accepted tokens are appended to the input and the model is called again.
5. Generation stops when the model emits a newline or an empty token.

Because only prefixes of real function names are accepted, the result is always
the name of a defined function. Which one it is remains the model's decision.

### 3. Choosing the parameters

For each parameter of the chosen function:

1. A candidate list is built from the prompt: its words, quoted strings,
   numbers, and a small table of keyword-to-pattern pairs (see Design
   decisions).
2. The model generates the value token by token. A token is accepted only if the
   text so far is a prefix of a candidate and matches the parameter type
   (`number` or `string`).
3. When exactly one candidate remains, it is used. Numbers are converted to
   `float`.
4. If too many tokens are rejected in a row (500), the parameter is set to
   `None`.

### 4. Writing the output

Each result is stored in an `OutputFunction` pydantic model (`prompt`, `name`,
`parameters`) and the list is written with `json.dump`.
the llm only creates the function name and parameter values the rest is created by the json.dump.

## Design decisions

- **Pydantic for every data class.** Required by the subject, and it validates
  input files early with clear errors.
- **Greedy selection with rejection.** The best-scoring token is tested and
  rejected if invalid. checking the all the options first was also tried but that increase the genration time instead choosing the best option and testing it
- **Candidates taken from the prompt for parameter values.** This keeps values
  grounded in the request and also keep the output consitent 
- **Keyword-to-pattern table (`additions`).** A small table maps words such as
  "vowels" to patterns such as `([aeiouAEIOU])`.
  this adds extra options for the llm to choose from if the request needs somthing with a diffrent name often for searching certain characters.
  if the input does not now if chooses the closed possible option to use.
- **Loading spinner in a separate thread.** Visual feedback during the slow
  model calls.

## Performance analysis

| Metric | Result |
| --- | --- |
| Accuracy (correct function and arguments) | TODO: 10 / 9 prompts (90%) |
| Total time for the test file | 113 sec |
| Time per prompt | 11 sec |

## Challenges faced

- understanding decision making of llm
	had problems with making the llm giving the right output I first tried a very detail rule promt but the subject states that have to filter more the anwsers so i choose for a set list the llm could choose from
- Knowing when a generated value is finished (stop condition)
	it is diffcult to know when subject has the anwser so I gave it a example it had to follow wich improved the output and could give me easy way to check

## Testing strategy

- Edge cases: empty strings, large and negative numbers, decimals, special
  characters, multi-word strings, quotes.
- Prompts that are ambiguous or match several functions.
- Different function sets and different prompt files.
- Missing or invalid input files, and wrong value types.
- Checking the output file: valid JSON, exact keys, argument types matching the
  definitions.
- Static checks: `make lint`.

## Example usage

```bash
# defaults
uv run python -m src

# custom paths
uv run python -m src \
    --functions_definition data/input/functions_definition.json \
    --input data/input/function_calling_tests.json \
    --output data/output/function_calls.json
```

Example input prompt and output entry:

```json
{
    "prompt": "Reverse the string 'hello'",
    "name": "fn_reverse_string",
    "parameters": {"s": "hello"}
}
```

## Resources

**References**
- fucntion calling with llm: https://www.promptingguide.ai/applications/function_calling
- qwen hugging fase: https://huggingface.co/Qwen/Qwen3-8B
- Python documentation: `argparse`, `json`
- Pydantic documentation: https://pydantic.dev/docs/validation/dev/concepts/json/
- explanation of common functions: https://www.w3schools.com/, https://www.geeksforgeeks.org/

**How AI was used**
- explaining concepts such as logits and tokenization.
- reviewing my reasoning and finding bugs.
- drafting the structure of this README.