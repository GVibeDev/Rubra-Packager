from __future__ import annotations

import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .config import android_work_root, default_output_dir
from .icons import decode_data_uri, write_android_icons
from .io_utils import atomic_write_json, read_json, sha256_file
from .models import BuildProfile
from .preflight import run_preflight
from .process import executable, run
from .security import parse_hex_color, safe_filename_stem, validate_package_name
from .source import resolve_static_source
from .staging import stage_source


class AndroidBuilder:
    @staticmethod
    def _java_candidates(env: dict[str, str] | None = None) -> list[Path]:
        env = env or os.environ.copy()
        candidates: list[Path] = []
        existing = env.get("JAVA_HOME")
        if existing:
            candidates.append(Path(existing))
        if os.name == "nt":
            program_files = Path(env.get("ProgramFiles", r"C:\Program Files"))
            local_app = Path(env.get("LOCALAPPDATA", ""))
            candidates.extend([
                program_files / "Android" / "Android Studio" / "jbr",
                local_app / "Programs" / "Android Studio" / "jbr",
                *sorted((program_files / "Eclipse Adoptium").glob("jdk-*")),
                *sorted((program_files / "Java").glob("jdk-*")),
                *sorted((program_files / "Microsoft").glob("jdk-*")),
            ])
        unique: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate).casefold()
            if key not in seen:
                seen.add(key)
                unique.append(candidate)
        return unique

    @staticmethod
    def _probe_java_home(home: Path) -> tuple[bool, str]:
        java = home / "bin" / ("java.exe" if os.name == "nt" else "java")
        if not java.exists():
            return False, "Java executable not found"
        probe = run([java, "-version"])
        raw = (probe.stderr or probe.stdout).strip()
        match = re.search(r'version "(\d+)', raw)
        major = int(match.group(1)) if match else 0
        return major >= 17, raw.splitlines()[0] if raw else str(java)

    @classmethod
    def prerequisites(cls) -> dict[str, Any]:
        result = {
            "java": {"ok": False, "message": "Not found"},
            "node": {"ok": False, "message": "Not found"},
            "sdk": {"ok": False, "message": "Not found"},
        }
        try:
            java = executable("java")
            probe = run([java, "-version"])
            raw = (probe.stderr or probe.stdout).strip()
            match = re.search(r'version "(\d+)', raw)
            major = int(match.group(1)) if match else 0
            result["java"] = {"ok": major >= 17, "message": raw.splitlines()[0] if raw else java}
        except Exception:
            for candidate in cls._java_candidates():
                ok, message = cls._probe_java_home(candidate)
                if message != "Java executable not found":
                    result["java"] = {"ok": ok, "message": message}
                    break
        try:
            node = executable("node")
            probe = run([node, "--version"])
            result["node"] = {"ok": probe.returncode == 0, "message": probe.stdout.strip() or node}
        except Exception as exc:
            result["node"]["message"] = str(exc)

        sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if not sdk and os.name == "nt":
            sdk = str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk")
        if sdk and Path(sdk).is_dir():
            result["sdk"] = {"ok": True, "message": str(Path(sdk).resolve())}
        result["allOk"] = all(result[key]["ok"] for key in ("java", "node", "sdk"))
        return result

    @classmethod
    def _java_env(cls, log: list[str]) -> dict[str, str]:
        env = os.environ.copy()
        for candidate in cls._java_candidates(env):
            ok, message = cls._probe_java_home(candidate)
            if ok:
                java = candidate / "bin" / ("java.exe" if os.name == "nt" else "java")
                env["JAVA_HOME"] = str(candidate)
                env["PATH"] = str(java.parent) + os.pathsep + env.get("PATH", "")
                log.append(f"JAVA_HOME: {candidate} ({message})")
                return env
        try:
            java = Path(executable("java"))
            env["JAVA_HOME"] = str(java.parent.parent)
            env["PATH"] = str(java.parent) + os.pathsep + env.get("PATH", "")
            log.append(f"JAVA_HOME from PATH: {env['JAVA_HOME']}")
        except Exception:
            pass
        return env

    @staticmethod
    def _write_capacitor_config(work: Path, app_name: str, package_name: str) -> None:
        payload = {
            "appId": package_name,
            "appName": app_name,
            "webDir": "www",
            "server": {"androidScheme": "https"},
        }
        (work / "capacitor.config.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    @staticmethod
    def _patch_manifest(manifest: Path, orientation: str) -> None:
        text = manifest.read_text(encoding="utf-8")
        if "android:screenOrientation" in text:
            text = re.sub(
                r'android:screenOrientation="[^"]+"',
                f'android:screenOrientation="{orientation}"',
                text,
                count=1,
            )
        else:
            text = text.replace(
                "<activity",
                f'<activity\n            android:screenOrientation="{orientation}"',
                1,
            )
        text = re.sub(r'android:usesCleartextTraffic="true"', 'android:usesCleartextTraffic="false"', text)
        manifest.write_text(text, encoding="utf-8", newline="\n")

    @staticmethod
    def _patch_app_strings(strings_xml: Path, app_name: str, package_name: str) -> None:
        if not strings_xml.exists():
            return
        text = strings_xml.read_text(encoding="utf-8")
        safe_name = escape(app_name)
        safe_package = escape(package_name)
        replacements = {
            "app_name": safe_name,
            "title_activity_main": safe_name,
            "package_name": safe_package,
            "custom_url_scheme": safe_package,
        }
        for key, value in replacements.items():
            pattern = rf'(<string\s+name="{re.escape(key)}"[^>]*>)(.*?)(</string>)'
            text, count = re.subn(pattern, rf'\g<1>{value}\g<3>', text, count=1, flags=re.S)
            if count == 0:
                text = text.replace("</resources>", f'    <string name="{key}">{value}</string>\n</resources>')
        strings_xml.write_text(text, encoding="utf-8", newline="\n")

    @staticmethod
    def _find_apksigner(sdk: Path) -> Path | None:
        build_tools = sdk / "build-tools"
        if not build_tools.is_dir():
            return None
        name = "apksigner.bat" if os.name == "nt" else "apksigner"
        for version in sorted(build_tools.iterdir(), reverse=True):
            candidate = version / name
            if candidate.exists():
                return candidate
        return None

    def build(
        self,
        *,
        project_root: Path,
        app_name: str,
        package_name: str,
        profile: BuildProfile,
        variant_id: str,
        icon_data: str | None,
        icon_background: str,
        allow_source_build: bool,
        output_dir: Path | None = None,
    ) -> dict[str, Any]:
        log: list[str] = []
        package_name = validate_package_name(package_name)
        icon_background = parse_hex_color(icon_background)
        static_source = resolve_static_source(project_root, allow_build=allow_source_build, log=log)
        variant = profile.variant(variant_id)
        work = android_work_root() / safe_filename_stem(app_name)
        www = work / "www"
        included, excluded = stage_source(static_source, www, variant)
        report = run_preflight(www, profile, variant.variant_id)
        if report.errors:
            return {"success": False, "error": "Android preflight failed", "preflight": report.to_dict(), "log": log}

        work.mkdir(parents=True, exist_ok=True)
        package_json = work / "package.json"
        if not package_json.exists():
            package_json.write_text(
                json.dumps({"name": safe_filename_stem(app_name).lower(), "private": True, "version": "1.0.0"}, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        npm = executable("npm")
        npx = executable("npx")
        log.append("Installing/updating Capacitor dependencies")
        install = run([npm, "install", "@capacitor/cli", "@capacitor/core", "@capacitor/android"], cwd=work)
        log.extend(line for line in install.stdout.splitlines()[-100:] if line.strip())
        if install.returncode != 0:
            return {"success": False, "error": "Capacitor installation failed", "log": log}

        self._write_capacitor_config(work, app_name, package_name)
        android = work / "android"
        build_state_path = work / ".rubra-android.json"
        previous_state = read_json(build_state_path, default={}) or {}
        if android.is_dir() and previous_state.get("packageName") not in (None, package_name):
            log.append("Android package name changed; recreating the native platform")
            shutil.rmtree(android)
        if not android.is_dir():
            added = run([npx, "cap", "add", "android"], cwd=work)
            log.extend(line for line in (added.stdout + "\n" + added.stderr).splitlines()[-120:] if line.strip())
            if added.returncode != 0:
                return {"success": False, "error": "Capacitor could not add the Android platform", "log": log}

        atomic_write_json(build_state_path, {"packageName": package_name, "appName": app_name})

        synced = run([npx, "cap", "sync", "android"], cwd=work)
        log.extend(line for line in (synced.stdout + "\n" + synced.stderr).splitlines()[-120:] if line.strip())
        if synced.returncode != 0:
            return {"success": False, "error": "Capacitor sync failed", "log": log}

        manifest = android / "app" / "src" / "main" / "AndroidManifest.xml"
        if manifest.exists():
            self._patch_manifest(manifest, profile.orientation)
        self._patch_app_strings(
            android / "app" / "src" / "main" / "res" / "values" / "strings.xml",
            app_name,
            package_name,
        )
        icon_count = 0
        if icon_data:
            res = android / "app" / "src" / "main" / "res"
            icon_count = len(write_android_icons(decode_data_uri(icon_data), res, icon_background))
            log.append(f"Generated {icon_count} Android icon resources")

        sdk_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if not sdk_value and os.name == "nt":
            sdk_value = str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk")
        sdk = Path(sdk_value or "")
        if not sdk.is_dir():
            return {"success": False, "error": "Android SDK was not found", "log": log}
        sdk_path = str(sdk.resolve()).replace("\\", "/")
        (android / "local.properties").write_text(
            f"sdk.dir={sdk_path}\n",
            encoding="utf-8",
            newline="\n",
        )

        gradlew = android / ("gradlew.bat" if os.name == "nt" else "gradlew")
        if not gradlew.exists():
            return {"success": False, "error": f"Gradle wrapper missing: {gradlew}", "log": log}
        env = self._java_env(log)
        assembled = run([gradlew, "assembleDebug"], cwd=android, env=env)
        log.extend(line for line in (assembled.stdout + "\n" + assembled.stderr).splitlines()[-220:] if line.strip())
        if assembled.returncode != 0:
            return {"success": False, "error": "Gradle assembleDebug failed", "log": log}

        apk = android / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
        if not apk.is_file():
            return {"success": False, "error": "Gradle completed but app-debug.apk was not found", "log": log}
        try:
            with zipfile.ZipFile(apk) as archive:
                bad = archive.testzip()
            if bad:
                raise RuntimeError(f"Corrupt APK entry: {bad}")
            log.append("APK ZIP integrity check passed")
        except Exception as exc:
            return {"success": False, "error": f"APK integrity check failed: {exc}", "log": log}

        signature = "not checked"
        signer = self._find_apksigner(sdk)
        if signer:
            verified = run([signer, "verify", "--verbose", apk])
            signature = "verified" if verified.returncode == 0 else "failed"
            if verified.returncode != 0:
                return {"success": False, "error": "APK signature verification failed", "log": log}
            log.append("APK debug signature verified")

        target_dir = (output_dir or default_output_dir()).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        published = target_dir / f"{safe_filename_stem(app_name)}.apk"
        shutil.copy2(apk, published)
        return {
            "success": True,
            "path": str(published),
            "bytes": published.stat().st_size,
            "sha256": sha256_file(published),
            "signature": signature,
            "customIcon": bool(icon_data),
            "iconResources": icon_count,
            "profile": profile.profile_id,
            "variant": variant.variant_id,
            "includedFiles": len(included),
            "excludedFiles": len(excluded),
            "preflight": report.to_dict(),
            "log": log,
        }
