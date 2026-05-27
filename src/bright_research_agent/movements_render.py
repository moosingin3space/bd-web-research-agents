from collections import defaultdict

from bright_research_agent.schemas import Movement, MovementReport


_BUCKET_RANK = {"breaking": 0, "recent": 1, "context": 2}


def _movement_sort_key(m: Movement) -> tuple[int, int]:
    return (-m.interestingness, _BUCKET_RANK.get(m.surfaced_in, 99))


def _format_top_line(idx: int, m: Movement) -> str:
    return (
        f"{idx}. **[{m.interestingness}] {m.organization}** — {m.headline}  "
        f"_({m.surfaced_in}, {m.movement_type})_"
    )


def _format_org_entry(m: Movement) -> list[str]:
    lines = [
        f"- **[{m.interestingness}] {m.movement_type} — {m.surfaced_in}**: {m.headline}",
        f"  {m.summary}",
        f"  _Rubric: {m.interestingness_rationale}_",
    ]
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
    out.append(f"# Tech Movements Report — {report.run_date}")
    out.append("")
    out.append(
        f"_Buckets: {bucket_summary}. {len(report.organizations_checked)} "
        "organizations checked._"
    )
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
