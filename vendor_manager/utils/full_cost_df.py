"""Get a DataFrame with all costs and cost coverages for all engagements."""

import pandas as pd

from engagements.models import Engagement


def get_full_cost_df():
    """Returns a DataFrame with all costs and cost coverages for all engagements."""
    engagement_costs_lst = []
    engagement_cost_coverage_lst = []

    engagements = Engagement.objects.all()
    for en in engagements:
        costs = en.costs
        for ca in costs:
            ca["Engagement"] = en
            ca["Order"] = en.order
            ca["Person"] = en.person
            ca["Company"] = ca["Order"].company
        engagement_costs_lst += costs

        cost_coverage = en.cost_coverage
        for ca in cost_coverage:
            ca["Engagement"] = en
            ca["Undertaking"] = ca["undertaking"]
        engagement_cost_coverage_lst += cost_coverage

    engagement_costs = pd.DataFrame(engagement_costs_lst)
    engagement_cost_coverage = pd.DataFrame(engagement_cost_coverage_lst)

    full_df = engagement_costs.merge(engagement_cost_coverage, on=["Engagement", "date"], how="left")
    full_df["cost"] = full_df["cost"]*full_df["percentage"]
    return full_df
