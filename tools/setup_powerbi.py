"""Configure an exported source project with an independently obtained data bundle."""
import argparse
import hashlib
import json
from pathlib import Path


def configure(project, bundle):
    project, bundle = Path(project).resolve(), Path(bundle).resolve()
    if project.name != 'ChargeScope.pbip' or not project.is_file():
        raise ValueError('Select the exported ChargeScope.pbip file.')
    metadata = project.parent / 'SOURCE_PACKAGE.json'
    if not metadata.is_file():
        raise ValueError('Only an exported source package may be configured; the working report is protected.')
    expected = json.loads(metadata.read_text(encoding='utf-8'))['required_csv_sha256']
    for name, digest in expected.items():
        source = bundle / name
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Missing or different pinned source: {name}')
    model_path = project.parent / 'ChargeScope.SemanticModel/model.bim'
    model = json.loads(model_path.read_text(encoding='utf-8'))
    expression = next(item for item in model['model']['expressions'] if item['name'] == 'BundlePath')
    expression['expression'] = '"' + str(bundle).replace('"', '""') + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    temporary = model_path.with_suffix('.bim.tmp')
    temporary.write_text(json.dumps(model, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(model_path)
    return project


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    print(configure(args.project, args.bundle))
