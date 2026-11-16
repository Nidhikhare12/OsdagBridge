"""Render the locally generated verification snapshot with the selected checkout."""
import os
import sys
import pickle
import subprocess
from pathlib import Path

if os.name == 'nt':
    handles = [os.add_dll_directory(str(Path(sys.prefix) / d))
               for d in ('Library/bin', 'DLLs') if (Path(sys.prefix) / d).is_dir()]
from osdagbridge.core.reports.report_generator import (
    ReportMetadata, ReportOptions, ReportRequest, build_report_payload, generate_report)

if __name__ == '__main__':
    case = pickle.loads((Path(__file__).parent / 'design_case.pkl').read_bytes())
    request = ReportRequest(
        ReportMetadata('20 m verification bridge', 'Custom verification site',
                       'OsdagBridge verification', 'Assignment comparison', 'OsdagBridge',
                       report_date='2026-11-15', job_number='VERIFY-20M'),
        ReportOptions(['loads', 'analysis', 'design_checks', 'drawings'], True, True, True),
        str(Path(sys.argv[2]).resolve()), sys.argv[1])
    payload = build_report_payload(request, case['inputs'], case['outputs'])
    original_run = subprocess.run
    def recorded_run(*args, **kwargs):
        result = original_run(*args, **kwargs)
        if args and isinstance(args[0], list) and 'pdflatex' in str(args[0][0]):
            log = Path(request.output_dir) / (request.file_stem + '.compiler.log')
            log.write_bytes(b'Exit code: ' + str(result.returncode).encode() + b'\n' +
                            (result.stdout or b'') + (result.stderr or b''))
        return result
    subprocess.run = recorded_run
    print(generate_report(payload, request), flush=True)
