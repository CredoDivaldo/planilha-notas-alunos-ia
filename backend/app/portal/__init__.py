"""Student Portal — read-only access to published academic data.

Portal rules:
  - AC-1: Read ONLY from publication_snapshots (is_current=True)
  - AC-2: Scope by authenticated student identity
  - AC-3: Aggregate by context/discipline
  - AC-4: Calendar from published_calendar_snapshots only
  - AC-5: No internal audit/draft history exposed
  - AC-6: Display formula metadata as-is, no recalc

No portal request shall ever read grade_entries, calculation_results,
or any internal state outside of published snapshots.
"""
