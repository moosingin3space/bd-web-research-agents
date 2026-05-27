import re
from collections import defaultdict

from bright_research_agent.schemas import Movement, MovementReport


_BUCKET_RANK = {"breaking": 0, "recent": 1, "context": 2}


def _movement_sort_key(m: Movement) -> tuple[int, int]:
    return (-m.interestingness, _BUCKET_RANK.get(m.surfaced_in, 99))


_NODE_ID_SANITIZER = re.compile(r"[^a-zA-Z0-9]+")


def _node_id(name: str) -> str:
    slug = _NODE_ID_SANITIZER.sub("_", name).strip("_").lower() or "node"
    return f"n_{slug}"


def _mermaid_escape(label: str) -> str:
    return label.replace('"', "'")


def render_mermaid(report: MovementReport) -> str:
    """Render a Mermaid flowchart of personnel movements (from -> to).

    Watchlist orgs are always rendered as nodes. External orgs named in
    `from_organization` / `to_organization` are added as nodes. Movements
    with no stated source or destination use an "Unknown" placeholder node.
    """
    watchlist = list(report.organizations_checked)
    watchlist_set = set(watchlist)

    edges: list[tuple[str, str, str]] = []  # (from, to, label)
    external_orgs: list[str] = []
    seen_external: set[str] = set()
    use_unknown = False

    sorted_movements = sorted(report.movements, key=_movement_sort_key)
    for m in sorted_movements:
        if not m.person_name:
            continue
        src = m.from_organization
        dst = m.to_organization
        if src is None and dst is None:
            continue

        if src is None:
            src_label = "Unknown"
            use_unknown = True
        else:
            src_label = src
            if src not in watchlist_set and src not in seen_external:
                external_orgs.append(src)
                seen_external.add(src)

        if dst is None:
            dst_label = "Unknown"
            use_unknown = True
        else:
            dst_label = dst
            if dst not in watchlist_set and dst not in seen_external:
                external_orgs.append(dst)
                seen_external.add(dst)

        edge_label = f"{m.person_name} [{m.interestingness}]"
        edges.append((src_label, dst_label, edge_label))

    lines: list[str] = ["flowchart LR"]

    if watchlist:
        lines.append("    %% Watchlist organizations")
        for org in watchlist:
            lines.append(f'    {_node_id(org)}["{_mermaid_escape(org)}"]')
    if external_orgs:
        lines.append("    %% External organizations")
        for org in external_orgs:
            lines.append(f'    {_node_id(org)}["{_mermaid_escape(org)}"]')
    if use_unknown:
        lines.append('    n_unknown(["Unknown"])')

    if edges:
        lines.append("    %% Movements")
        for src, dst, label in edges:
            src_id = "n_unknown" if src == "Unknown" else _node_id(src)
            dst_id = "n_unknown" if dst == "Unknown" else _node_id(dst)
            lines.append(f'    {src_id} -- "{_mermaid_escape(label)}" --> {dst_id}')
    else:
        lines.append("    %% No directed movements to render.")

    if watchlist:
        lines.append("    classDef watchlist fill:#dbeafe,stroke:#1e3a8a;")
        watchlist_ids = ",".join(_node_id(o) for o in watchlist)
        lines.append(f"    class {watchlist_ids} watchlist;")

    return "\n".join(lines)


def _format_top_line(idx: int, m: Movement) -> str:
    return (
        f"{idx}. **[{m.interestingness}] {m.organization}** — {m.headline}  "
        f"_({m.surfaced_in}, {m.movement_type})_"
    )


def _format_org_entry(m: Movement) -> list[str]:
    lines = [
        f"- **[{m.interestingness}] {m.movement_type} — {m.surfaced_in}**: {m.headline}",
        f"  {m.summary}",
    ]
    if m.person_name or m.from_organization or m.to_organization:
        flow = m.from_organization or "?"
        flow += f" → {m.to_organization or '?'}"
        person = m.person_name or "(unnamed)"
        lines.append(f"  _Move: {person} | {flow}_")
    lines.append(f"  _Rubric: {m.interestingness_rationale}_")
    if m.occurred_on:
        lines.append(f"  _Date: {m.occurred_on}_")
    lines.append(f"  _Confidence: {m.confidence}_")
    if m.citations:
        urls = ", ".join(c.url for c in m.citations)
        lines.append(f"  Sources: {urls}")
    return lines


def render_markdown(report: MovementReport) -> str:
    sorted_movements = sorted(report.movements, key=_movement_sort_key)
    bucket_summary = ", ".join(
        f"{name} ({window})" for name, window in report.buckets.items()
    )

    out: list[str] = []
    out.append(f"# Tech Personnel Movements Report — {report.run_date}")
    out.append("")
    out.append(
        f"_Buckets: {bucket_summary}. {len(report.organizations_checked)} "
        "organizations checked._"
    )
    out.append("")

    out.append("## Movement Map")
    out.append("")
    out.append("```mermaid")
    out.append(render_mermaid(report))
    out.append("```")
    out.append("")

    out.append("## Top Movements")
    if sorted_movements:
        for idx, m in enumerate(sorted_movements, start=1):
            out.append(_format_top_line(idx, m))
    else:
        out.append("_No notable movements surfaced this run._")
    out.append("")

    out.append("## By Organization")
    out.append("")
    by_org: dict[str, list[Movement]] = defaultdict(list)
    for m in sorted_movements:
        by_org[m.organization].append(m)

    org_order = [o for o in report.organizations_checked if o in by_org] + [
        o for o in by_org.keys() if o not in report.organizations_checked
    ]
    for org in org_order:
        out.append(f"### {org}")
        for m in by_org[org]:
            out.extend(_format_org_entry(m))
        out.append("")

    out.append("## Coverage Gaps")
    if report.coverage_gaps:
        for gap in report.coverage_gaps:
            out.append(f"- {gap}")
    else:
        out.append("_None._")
    out.append("")

    out.append("## Organizations With No Notable Movement")
    if report.zero_movement_orgs:
        for org in report.zero_movement_orgs:
            out.append(f"- {org}")
    else:
        out.append("_None._")
    out.append("")

    return "\n".join(out)
