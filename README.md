The goal of the proxy mock is provide local aternative for simulating Altinn service. 

Demo localhost:

```

#run proxy
docker-compose up -d nginx-altinn-proxy-mock

#test (legacy Altinn proxy endpoints - require X-API-Key)
curl -H "X-API-Key: <API_KEY>" "http://localhost:8128/api/serviceowner/reportees?ForceEIAuthentication&subject=01066800187&servicecode=4814&serviceedition=3"

#v2 mock endpoint for maskinporten token
curl "http://localhost:8128/api/maskinporten/token?scope=altinn:accessmanagement/authorizedparties.resourceowner"

#v2 authorizedparties (filtered by request-body value)
curl -X POST "http://localhost:8128/accessmanagement/api/v1/resourceowner/authorizedparties?includeAltinn3=true&includeResources=true" \
  -H "Authorization: Bearer demo-static-maskinporten-token" \
  -H "Content-Type: application/json" \
  -d '{"type":"urn:altinn:person:identifier-no","value":"01066800187"}'
```

Regenerate v2 data from legacy mockdata:

```
python3 scripts/generate_mockdata_v2.py
```

The generator reads:
- `mockdata/*.json` (subjects/reportees)
- `mockdata/authorization-mock/*.json` (legacy Rights/ServiceCode)

And writes:
- `mockdataV2/authorizedparties.json` (superset fallback)
- `mockdataV2/by-ssn/<ssn>.json` (filtered response source per person)

Legacy `ServiceCode` is mapped to Access Management `authorizedResources` like this:
- `5977` -> `datanorge-virksomhetsadministrator` (Admin)
- `5755` -> `datanorge-skrivetilgang` (Write)
- `5756` -> `datanorge-lesetilgang` (Read)
