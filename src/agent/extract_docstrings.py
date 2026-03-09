from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage,
    BaseMessage,
)
from pathlib import Path
import inspect
import diffpy.srfit.pdf
import diffpy.srfit.fitbase
import diffpy.srfit.structure
import diffpy.structure
import json

OUT_DIR = Path("doc_summaries")
OUT_DIR.mkdir(parents=True, exist_ok=True)
llm = ChatOpenAI(model="gpt-4-0613", temperature=0.2)
system_prompt = """
You are a helpful assistant for summarizing docstrings of python classes and methods.

For classes, you have to summarize the purpose, usage, and imporant methods and attributes
for that class. If they are not provided in the docstring, skip. 

For methods, you have to summarize the purpose, usage, input parameters and return values
for that method. If they are not provided in the docstring, skip.

You should only return the summary, and without any additional explanation. 
The summary should be concise and clear.
"""
system_msg = SystemMessage(content=system_prompt)


def summarize_docstring(name: str, kind: str, obj) -> str:
    doc = inspect.getdoc(obj)
    if not doc:
        return "(No docstring provided.)"
    human_msg = HumanMessage(content=f"{kind}: {name}\n\n{doc}")
    return llm.invoke([system_msg, human_msg]).content.strip()


def iter_declared_public_methods(cls):
    # Only methods declared on this class (not inherited), excluding private/dunder
    for method_name, member in cls.__dict__.items():
        if method_name.startswith("_"):
            continue

        fn = None
        if isinstance(member, staticmethod):
            fn = member.__func__
        elif isinstance(member, classmethod):
            fn = member.__func__
        elif inspect.isfunction(member):
            fn = member

        if fn is not None:
            yield method_name, fn


def write_class_summary_file(cls, out_dir: Path):
    class_name = f"{cls.__module__}.{cls.__name__}"
    class_summary = summarize_docstring(class_name, "Class", cls)

    records = [
        {
            "name": class_name,
            "kind": "class",
            "content": class_summary,
        }
    ]

    methods = list(iter_declared_public_methods(cls))
    for method_name, method_obj in methods:
        method_full_name = f"{class_name}.{method_name}"
        method_summary = summarize_docstring(
            method_full_name, "Method", method_obj
        )
        records.append(
            {
                "name": method_full_name,
                "kind": "method",
                "content": method_summary,
            }
        )

    out_file = out_dir / f"{cls.__name__}.json"
    out_file.write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote: {out_file}")


def write_function_summary_file(fn, out_dir: Path):
    function_name = f"{fn.__module__}.{fn.__name__}"
    function_summary = summarize_docstring(function_name, "Function", fn)

    records = [
        {
            "name": function_name,
            "kind": "function",
            "content": function_summary,
        }
    ]

    out_file = out_dir / f"{function_name.replace('.', '_')}.json"
    out_file.write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote: {out_file}")


# Option A: explicit class list
target_classes = [
    diffpy.srfit.pdf.DebyePDFGenerator,
    diffpy.srfit.pdf.PDFContribution,
    diffpy.srfit.pdf.PDFGenerator,
    diffpy.srfit.pdf.PDFParser,
    diffpy.srfit.fitbase.Calculator,
    diffpy.srfit.fitbase.FitContribution,
    diffpy.srfit.fitbase.FitHook,
    diffpy.srfit.fitbase.FitRecipe,
    diffpy.srfit.fitbase.FitResults,
    diffpy.srfit.fitbase.PlotFitHook,
    diffpy.srfit.fitbase.Profile,
    diffpy.srfit.fitbase.ProfileGenerator,
    # Add more classes here
]

# Option B: all classes defined in module
target_functions = [
    diffpy.srfit.structure.constrainAsSpaceGroup,
    diffpy.srfit.structure.sgconstraints,
    diffpy.srfit.structure.struToParameterSet,
    diffpy.structure.getParser,
    diffpy.structure.loadStructure,
    diffpy.structure.parsers,
    diffpy.structure.structure,
]

# for i, cls in enumerate(target_classes):
#     write_class_summary_file(cls, OUT_DIR)
#     print(f"Processed {i+1}/{len(target_classes)} classes.")

for i, fn in enumerate(target_functions):
    write_function_summary_file(fn, OUT_DIR)
    print(f"Processed {i+1}/{len(target_functions)} functions.")
