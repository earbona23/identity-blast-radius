# identity-blast-radius

Answers one question about one account: **if this person gets phished, what does the
attacker reach?** It maps a single Entra ID identity's blast radius — roles held, roles
one step away, permissions inherited from apps they own, groups they can alter — into a
one-screen report. Read-only, and a test enforces that.

> **Status: snapshot.** Feature-complete for what it does and its tests pass; last
> substantive change September 2026. I am not adding features here, and issues are welcome
> and read. Under active maintenance instead: [revtriage](https://github.com/earbona23/revtriage),
> [entra-tripwire](https://github.com/earbona23/entra-tripwire),
> [entraform](https://github.com/earbona23/entraform) and
> [vantage](https://github.com/earbona23/vantage).

## The problem

The account that gets phished is rarely a Global Admin — it's someone whose title says
"Marketing Analyst" and whose real reach nobody has ever added up. She's eligible (via PIM)
for a privileged role. She owns an app registration that holds `Mail.Read`, so whoever
controls her can add a credential to that app and read everyone's mail. She's in a
role-assignable group that grants Helpdesk Administrator. None of that is visible from her
profile, and it's exactly what an attacker enumerates first. This tool does that
enumeration for the defender.

## This is not BloodHound

BloodHound maps attack paths across the whole tenant and is the right tool for that. This
is deliberately the opposite: **one identity, defender-oriented, no ingestion, one page.**
You ask "what's the blast radius of this account?" and get a direct answer in seconds. If
you need full graph analysis, use BloodHound; if you need to triage a single account fast —
during an incident, an access review, or an onboarding — this is lighter.

## See it in 10 seconds — no tenant required

```bash
git clone https://github.com/earbona23/identity-blast-radius
cd identity-blast-radius
python -m blast.cli --demo
```

The demo identity is a marketing analyst whose blast radius reaches far past her title:

```
Severidad : ALTO
LO QUE ALCANZA EL ATACANTE:
  [alto]   puede ACTIVAR (PIM): User Administrator
  [alto]   miembro de grupo asignable a rol: Soporte Nivel 1 (rol)
  [alto]   posee la app: Reporting Sync → Mail.Read
  [medio]  posee el grupo (puede alterar membresía): Campañas 2026
  [bajo]   rol activo: Directory Readers
```

![Demo output](docs/screenshot.png)

## Use it on a real account

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
export IBR_CLIENT_SECRET=...

python -m blast.cli --live ana@contoso.com
python -m blast.cli --live ana@contoso.com --json ana.json
```

It exits `1` when the blast radius reaches `alto` or `critico`, so you can wire it into an
onboarding or access-review check.

## How the radius is computed

Reach is organized by **how close it is**, because not all of it is equal:

1. **Right now** — directory roles the account already holds.
2. **One step away** — roles it can *activate* (PIM-eligible), or reach by being a member of
   a role-assignable group. One step is still blast radius.
3. **Inherited from owned apps** — owning an app registration means you can add credentials
   to it, i.e. act as it. So the account effectively holds that app's application
   permissions. An owned app with `Mail.Read` is a mail-read path, and this is the reach
   people miss most.
4. **Can modify** — groups the account owns and whose membership it can change.

Severity is the highest level reachable by any of those paths. Which roles and app
permissions count as high-value lives in [`rules/high_value.yaml`](rules/high_value.yaml),
an editable catalog — a role or permission it doesn't know is shown but doesn't inflate the
radius.

### Permissions — read-only

`User.Read.All`, `GroupMember.Read.All`, `Application.Read.All`,
`RoleManagement.Read.Directory`. The Graph client exposes only `get()`/`get_all()`, and
`tests/test_readonly_guarantee.py` fails if a write verb appears anywhere. It maps the
account; it never activates a role or changes a membership.

## Limitations

- **One identity at a time, by design.** It does not compute tenant-wide paths or
  chains between accounts — that's BloodHound's job, and this doesn't pretend to replace it.
- **It reads standing reach, not runtime access.** Data-plane grants (a specific mailbox
  delegation, a SharePoint permission set on one site) aren't fully enumerable from these
  directory reads; the tool covers the directory-level radius and says so rather than
  implying completeness.
- **PIM eligibility depends on licensing/permission.** Where the eligibility read isn't
  available, the tool omits it rather than asserting an account has no eligible roles.
- **`--live` is unit-tested with mocked Graph responses.** Validate against your tenant
  before relying on it operationally.

## Contributing

New entries in the high-value catalog are welcome — add the role or permission and its
level. Keep collectors read-only. Run `pytest -q` and `ruff check .`.

## License

MIT — see [LICENSE](LICENSE).
