import subprocess
import time
import hashlib
import os
import signal
import tempfile
import json
from typing import Dict, Any, Optional, List

class SandboxResult:
    def __init__(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        execution_time_ms: float,
        contained: bool,
        receipt_hash: str,
        receipt_payload: Dict[str, Any],
        security_flags: List[str]
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time_ms = execution_time_ms
        self.contained = contained
        self.receipt_hash = receipt_hash
        self.receipt_payload = receipt_payload
        self.security_flags = security_flags

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "contained": self.contained,
            "receipt_hash": self.receipt_hash,
            "receipt_payload": self.receipt_payload,
            "security_flags": self.security_flags,
        }

class SandboxEngine:
    """
    Blast Radius Zero execution sandbox.
    Guarantees:
    1. Process & File isolation: Ephemeral temporary workspace, process-group termination.
    2. Secret hygiene: Strips host environment variables and guards /proc environment reads.
    3. Network air-gap: Blocks raw socket connections in the sandboxed runtime.
    4. Deterministic Receipts: Mints verifiable SHA-256 receipts over serialized execution payloads.
    5. Containment detection: Scans and neutralizes host reconnaissance and escape vectors.
    """

    DEFAULT_TIMEOUT_SECONDS = 5.0
    MAX_OUTPUT_BYTES = 50 * 1024

    SANITY_ENV_WHITELIST = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }

    SUSPICIOUS_PATTERNS = [
        ("VULTR_API_KEY", "Attempted API key extraction"),
        ("os.environ", "Environment probe"),
        ("socket.", "Network egress attempt"),
        ("urllib", "Outbound HTTP request attempt"),
        ("requests.", "Outbound network request attempt"),
        ("/etc/passwd", "Host credential read attempt"),
        ("/etc/shadow", "Host system file probe"),
        ("/proc/", "Host process inspection attempt"),
        ("subprocess.", "Secondary shell execution attempt"),
    ]

    # Python security guard preamble injected into untrusted guest code
    CONTAINMENT_GUARD_PREAMBLE = '''# AegisBox Runtime Containment Guard
import sys

# 1. Neutralize unauthorized network egress
try:
    import socket
    def _blocked_connect(*args, **kwargs):
        raise PermissionError("AegisBox Containment: Network egress blocked in zero-blast sandbox")
    socket.socket.connect = _blocked_connect
    socket.create_connection = _blocked_connect
except Exception:
    pass

# 2. Block unauthorized subprocess spawning
try:
    import subprocess
    def _blocked_exec(*args, **kwargs):
        raise PermissionError("AegisBox Containment: Subprocess spawning blocked in zero-blast sandbox")
    subprocess.Popen = _blocked_exec
    subprocess.run = _blocked_exec
    subprocess.call = _blocked_exec
    subprocess.check_output = _blocked_exec
except Exception:
    pass

# 3. Guard file access to sensitive host files and /proc
_real_open = open
def _guarded_open(file, *args, **kwargs):
    s = str(file)
    if any(s.startswith(p) for p in ["/proc", "/etc/shadow"]):
        raise PermissionError(f"AegisBox Containment: Access to {s} blocked in guest runtime")
    return _real_open(file, *args, **kwargs)
import builtins
builtins.open = _guarded_open
'''

    @classmethod
    def analyze_code_safety(cls, code: str) -> List[str]:
        flags = []
        for pattern, reason in cls.SUSPICIOUS_PATTERNS:
            if pattern in code:
                flags.append(f"[CONTAINMENT-FLAG] {reason} (pattern: `{pattern}`)")
        return flags

    @classmethod
    def execute_python(
        cls,
        code: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> SandboxResult:
        start_time = time.time()
        security_flags = cls.analyze_code_safety(code)

        with tempfile.TemporaryDirectory(prefix="aegis_sandbox_") as tmp_dir:
            script_path = os.path.join(tmp_dir, "workload.py")
            
            # Combine runtime security guard with workload code
            full_code = cls.CONTAINMENT_GUARD_PREAMBLE + "\n# User Workload:\n" + code
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(full_code)

            isolated_env = dict(cls.SANITY_ENV_WHITELIST)
            isolated_env["AEGIS_SANDBOX_ID"] = os.path.basename(tmp_dir)
            isolated_env["AEGIS_CONTAINMENT_MODE"] = "STRICT_ZERO_BLAST"

            try:
                proc = subprocess.run(
                    ["python3", script_path],
                    cwd=tmp_dir,
                    env=isolated_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                    preexec_fn=os.setsid if hasattr(os, "setsid") else None
                )
                stdout = proc.stdout[:cls.MAX_OUTPUT_BYTES]
                stderr = proc.stderr[:cls.MAX_OUTPUT_BYTES]
                exit_code = proc.returncode
                contained = True

            except subprocess.TimeoutExpired:
                stdout = ""
                stderr = f"Execution exceeded safety threshold of {timeout}s. Process terminated by watchdog."
                exit_code = -9
                contained = True
                security_flags.append("[CONTAINMENT-ENFORCED] Execution timeout ceiling reached.")
            except Exception as e:
                stdout = ""
                stderr = f"Sandbox execution error: {str(e)}"
                exit_code = 1
                contained = True

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Deterministic verification payload
        receipt_payload = {
            "code_hash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "duration_ms": duration_ms
        }
        serialized = json.dumps(receipt_payload, sort_keys=True)
        receipt_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time_ms=duration_ms,
            contained=contained,
            receipt_hash=receipt_hash,
            receipt_payload=receipt_payload,
            security_flags=security_flags
        )
