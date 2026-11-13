"""Refresh the checked-in API signatures using the selected PANDA installation."""

import argparse
import importlib
import inspect
import json
import re
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Annotated, Union, get_args, get_origin

import panda_md

from api_reference import API_GROUPS, METADATA_PATH


MEMBER_NOTES = {
    "default_optimize": "The parameter names optimized by default for this shape.",
    "phi_limits": "Lower and upper volume-fraction limits for the supplied parameters.",
    "surface_terms": "Return the interfacial areas used in the capillary-energy calculation.",
    "capillary_energy": "Compute the relative capillary energy from the model's surface terms.",
    "fit": "Fit this model to a density profile with the specified optimization settings.",
    "summary": "Return a human-readable summary of the result and its diagnostics.",
    "mean": "Return the mean over blocks.",
    "block_count": "Number of available profiles or time blocks.",
    "coordinate_nm": "Common bin centers in nm.",
    "fitted": "Successful candidate fits, in ranking order.",
    "best": "The lowest-loss fitted candidate.",
    "table": "Format the accuracy metrics as a text table.",
    "SlitPore.from_trajectory": "Measure the wall-to-wall gap and box lengths from a selected trajectory frame.",
    "CylinderPore.from_trajectory": "Measure the tube diameter and periodic length from the wall selection.",
}


def resolve(qualified):
    if qualified == "panda_md.InterfaceModel.fit":
        return panda_md.InterfaceModel.fit
    module, _, name = qualified.rpartition(".")
    return getattr(importlib.import_module(module), name)


def annotation_text(value):
    if value is inspect.Parameter.empty:
        return ""
    if value is Ellipsis:
        return "..."
    if value is None or value is type(None):
        return "None"
    origin = get_origin(value)
    arguments = get_args(value)
    if origin is Annotated:
        return annotation_text(arguments[0])
    if origin in (Union, UnionType):
        return " | ".join(annotation_text(item) for item in arguments)
    if origin is not None:
        if getattr(origin, "__name__", "") == "ndarray":
            dtype = get_args(arguments[1])
            return f"NDArray[{annotation_text(dtype[0])}]" if dtype else "NDArray"
        name = getattr(origin, "__name__", str(origin))
        return f"{name}[{', '.join(annotation_text(item) for item in arguments)}]"
    annotation = value if isinstance(value, str) else inspect.formatannotation(value)
    if len(annotation) >= 2 and annotation[0] == annotation[-1] and annotation[0] in "'\"":
        annotation = annotation[1:-1]
    return re.sub(r"\b(?:typing|collections\.abc|(?:panda_md|numpy|matplotlib)(?:\.\w+)*?)\.(?=\w)", "", annotation)


def signature(name, obj):
    try:
        definition = inspect.signature(obj)
    except (ValueError, TypeError):
        return ""
    parameters = []
    fields = getattr(obj, "model_fields", {})
    for argument in definition.parameters.values():
        if argument.name in {"self", "cls"}:
            continue
        field = fields.get(argument.name)
        annotation = annotation_text(field.annotation if field is not None else argument.annotation)
        if field is not None and field.default_factory in (dict, list, set, tuple):
            default = f"{field.default_factory.__name__}()"
        elif isinstance(argument.default, Enum):
            default = f"{type(argument.default).__name__}.{argument.default.name}"
        elif argument.default is not inspect.Parameter.empty:
            default = repr(argument.default)
        else:
            default = ""
        parameters.append(argument.replace(
            annotation=SignatureText(annotation) if annotation else inspect.Parameter.empty,
            default=SignatureText(default) if default else inspect.Parameter.empty,
        ))
    returned = annotation_text(definition.return_annotation)
    cleaned = definition.replace(parameters=parameters, return_annotation=inspect.Signature.empty)
    text = f"{name}{cleaned}" + (f" -> {returned}" if returned else "")
    if len(text) <= 96:
        return text
    lines = []
    previous = None
    for argument in parameters:
        kind = argument.kind
        if previous is inspect.Parameter.POSITIONAL_ONLY and kind is not previous:
            lines.append("/")
        if kind is inspect.Parameter.KEYWORD_ONLY and previous not in {
            inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_POSITIONAL,
        }:
            lines.append("*")
        lines.append(str(argument))
        previous = kind
    if previous is inspect.Parameter.POSITIONAL_ONLY:
        lines.append("/")
    ending = f" -> {returned}" if returned else ""
    return name + "(\n    " + ",\n    ".join(lines) + ",\n)" + ending


class SignatureText:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.text


def source_location(obj):
    try:
        path = Path(inspect.getsourcefile(obj))
        line = inspect.getsourcelines(obj)[1]
        relative = path.relative_to(Path(panda_md.__file__).parent.parent)
    except (TypeError, OSError, ValueError):
        return ""
    return f"src/{relative.as_posix()}#L{line}"


def member_metadata(obj, name):
    member = getattr(obj, name)
    raw = inspect.getattr_static(obj, name)
    if isinstance(raw, property):
        annotation = annotation_text(inspect.signature(raw.fget).return_annotation)
        rendered = f"{name}: {annotation}" if annotation else name
    else:
        rendered = signature(name, member)
    doc = inspect.getdoc(member)
    note = MEMBER_NOTES.get(f"{obj.__name__}.{name}") or MEMBER_NOTES.get(name)
    description = note or (doc.splitlines()[0] if doc else "")
    return {"signature": rendered, "description": description}


def main(commit):
    symbols = {}
    for _, _, _, _, _, entries in API_GROUPS:
        for qualified, _, members in entries:
            obj = resolve(qualified)
            name = qualified.rsplit(".", 1)[-1]
            is_class = inspect.isclass(obj)
            is_enum = is_class and issubclass(obj, Enum)
            is_error = is_class and issubclass(obj, BaseException)
            info = {"name": qualified, "source": source_location(obj)}
            if not (is_enum or is_error or name == "__version__"):
                info["signature"] = signature(name, obj)
            if is_enum:
                info["values"] = [(entry.name, str(entry.value)) for entry in obj]
            if is_class and getattr(obj, "model_fields", None):
                info["fields"] = [
                    (field, annotation_text(spec.annotation)) for field, spec in obj.model_fields.items()
                ]
            if members:
                info["members"] = {name: member_metadata(obj, name) for name in members.split()}
            symbols[qualified] = info

    exports = {f"panda_md.{name}" for name in panda_md.__all__}
    if missing := exports - symbols.keys():
        raise ValueError(f"Missing top-level PANDA symbols: {sorted(missing)}")
    METADATA_PATH.write_text(
        json.dumps({"commit": commit, "symbols": symbols}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", help="Git commit of the PANDA checkout being documented")
    main(parser.parse_args().commit)
