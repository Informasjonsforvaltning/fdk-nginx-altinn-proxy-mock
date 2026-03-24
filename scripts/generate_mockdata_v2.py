#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "mockdata"
LEGACY_RIGHTS_DIR = LEGACY_DIR / "authorization-mock"
V2_DIR = ROOT / "mockdataV2"
V2_BY_SSN_DIR = V2_DIR / "by-ssn"

SSN_RE = re.compile(r"^\d{11}$")
ORGNR_RE = re.compile(r"^\d{9}$")

SERVICE_CODE_TO_RESOURCE = {
    "5977": "datanorge-virksomhetsadministrator",  # admin
    "5755": "datanorge-skrivetilgang",             # write
    "5756": "datanorge-lesetilgang",               # read
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def stable_uuid(namespace: str, value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{value}"))


def parse_rights() -> dict[str, set[str]]:
    resources_by_org: dict[str, set[str]] = {}
    for file in sorted(LEGACY_RIGHTS_DIR.glob("*.json")):
        data = load_json(file)
        if not isinstance(data, dict):
            continue
        reportee = data.get("Reportee", {})
        if not isinstance(reportee, dict):
            continue
        orgnr = str(reportee.get("OrganizationNumber") or "").strip()
        if not ORGNR_RE.match(orgnr):
            continue

        rights = data.get("Rights", [])
        if not isinstance(rights, list):
            continue
        for right in rights:
            if not isinstance(right, dict):
                continue
            code = str(right.get("ServiceCode") or "").strip()
            resource = SERVICE_CODE_TO_RESOURCE.get(code)
            if resource:
                resources_by_org.setdefault(orgnr, set()).add(resource)
    return resources_by_org


def person_party(name: str, ssn: str) -> dict[str, Any]:
    return {
        "partyUuid": stable_uuid("person", ssn),
        "name": name,
        "organizationNumber": None,
        "personId": ssn,
        "type": "Person",
        "unitType": None,
        "isDeleted": False,
        "authorizedResources": [],
    }


def org_party(name: str, orgnr: str, orgform: str | None, resources: list[str]) -> dict[str, Any]:
    return {
        "partyUuid": stable_uuid("org", orgnr),
        "name": name,
        "organizationNumber": orgnr,
        "personId": None,
        "type": "Organization",
        "unitType": orgform,
        "isDeleted": False,
        "authorizedResources": resources,
    }


def main() -> int:
    resources_by_org = parse_rights()

    superset_people: dict[str, dict[str, Any]] = {}
    superset_orgs: dict[str, dict[str, Any]] = {}

    files_by_ssn = sorted(LEGACY_DIR.glob("*.json"))
    for file in files_by_ssn:
        data = load_json(file)
        if not isinstance(data, list):
            continue

        ssn = file.stem
        if not SSN_RE.match(ssn):
            continue

        person_name = None
        local_orgs: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            etype = entry.get("Type")
            if etype == "Person":
                candidate = str(entry.get("SocialSecurityNumber") or "").strip()
                if candidate == ssn:
                    person_name = str(entry.get("Name") or "").strip() or ssn
            elif etype in ("Enterprise", "Organization"):
                orgnr = str(entry.get("OrganizationNumber") or "").strip()
                if not ORGNR_RE.match(orgnr):
                    continue
                org_name = str(entry.get("Name") or "").strip() or orgnr
                orgform = entry.get("OrganizationForm")
                orgform = str(orgform).strip() if orgform is not None else None
                resources = sorted(resources_by_org.get(orgnr, set()))
                org_obj = org_party(org_name, orgnr, orgform, resources)
                local_orgs.append(org_obj)
                superset_orgs.setdefault(orgnr, org_obj)

        if person_name is None:
            person_name = ssn

        person_obj = person_party(person_name, ssn)
        superset_people.setdefault(ssn, person_obj)

        payload = [person_obj] + sorted(local_orgs, key=lambda o: o["organizationNumber"] or "")
        write_json(V2_BY_SSN_DIR / f"{ssn}.json", payload)

    superset = sorted(superset_people.values(), key=lambda p: p["personId"] or "") + sorted(
        superset_orgs.values(), key=lambda o: o["organizationNumber"] or ""
    )
    write_json(V2_DIR / "authorizedparties.json", superset)

    print(f"Wrote {V2_DIR / 'authorizedparties.json'} ({len(superset)} entries)")
    print(f"Wrote {len(list(V2_BY_SSN_DIR.glob('*.json')))} by-ssn files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

