"""Summary dashboard class."""

import pandas as pd
import plotly.express as px
from django import forms

from companies.models import Company
from engagements.models import Engagement
from orders.models import Order
from people.models import Person
from undertakings.models import Undertaking
from vendor_manager.utils.full_cost_df import get_full_cost_df


class SummaryDashboard:
    """Class for the summary dashboard."""

    class ControlForm(forms.Form):
        """Form for the summary dashboard."""

        CLASSES = [Engagement, Undertaking, Person, Order, Company]
        GRANULARITY_CHOICES = [
            ("Monthly", "Monthly"),
            ("Daily", "Daily"),
            ("Total", "Total"),
        ]
        class_ = forms.ChoiceField(choices=[(c.__name__, c.__name__) for c in CLASSES], label="Class", required=False)
        granularity = forms.ChoiceField(choices=GRANULARITY_CHOICES, label="Granularity", required=False)
        min_date = forms.DateField(label="Min Date", required=False)
        max_date = forms.DateField(label="Max Date", required=False)

        def __init__(self, full_df, *args, **kwargs):
            """Initialize the form."""
            super().__init__(*args, **kwargs)
            for class_ in self.CLASSES:
                unique = full_df[class_.__name__].unique()
                choices = [(getattr(u, "id", None), u) for u in unique]
                choices.insert(0, ("all", "All"))
                self.fields[class_.__name__] = forms.MultipleChoiceField(
                    choices=choices,
                    label=class_.__name__,
                    required=False,
                )

    def __init__(self, **kwargs):
        """Initialize the summary dashboard."""
        self.full_df = get_full_cost_df()
        self.__class_param = Undertaking
        self.update(form=self.get_form())

    def recalculate(self):
        """Recalculate the summary table and plot."""
        self.full_df = get_full_cost_df()

    def update(self, form):
        """Update the summary table and plot based on the form data."""
        if form.is_valid():
            self.__class_param = globals().get(form.cleaned_data.get("class_", "Undertaking"))
            self.__granularity = form.cleaned_data.get("granularity", "Total")
            self.min_date = form.cleaned_data.get("min_date")
            self.max_date = form.cleaned_data.get("max_date")

            self.filters = {}
            for class_ in form.CLASSES:
                ids = form.cleaned_data.get(class_.__name__, ["all"])
                if "all" in ids:
                    self.filters[class_.__name__] = []
                else:
                    self.filters[class_.__name__] = [class_.objects.get(id=identifier) for identifier in ids]
        else:
            raise ValueError(f"Invalid form data {form.errors}")

        filtered_df = self.full_df

        if self.min_date:
            filtered_df = filtered_df[filtered_df["date"] >= self.min_date]
        if self.max_date:
            filtered_df = filtered_df[filtered_df["date"] <= self.max_date]

        for class_name, values in self.filters.items():
            if values:
                filtered_df = filtered_df[filtered_df[class_name].isin(values)]

        filtered_df["id"] = filtered_df[self.__class_param.__name__].apply(lambda x: getattr(x, "id", None))

        if self.__granularity == "Monthly":
            filtered_df["month"] = filtered_df["date"].apply(lambda x: x.strftime("%Y-%m"))
            grouped_df = filtered_df.groupby(["id", "month"], as_index=False, dropna=False).agg({"cost": "sum"})
        elif self.__granularity == "Daily":
            grouped_df = filtered_df.groupby(["id", "date"], as_index=False, dropna=False).agg({"cost": "sum"})
        else:
            grouped_df = filtered_df.groupby("id", as_index=False, dropna=False).agg({"cost": "sum"})

        grouped_df[self.__class_param.__name__] = grouped_df["id"].map(lambda x: self.__class_param.objects.get(id=x) if not pd.isna(x) else None)
        grouped_df["name"] = grouped_df[self.__class_param.__name__].apply(str)
        grouped_df.reset_index(drop=True, inplace=True)

        self.__summary_table = grouped_df

    def get_form(self, data={}):
        """Return the form."""
        if len(data) == 0:
            data = {
                "class_": "Undertaking",
                "granularity": "Total",
            }
        form = self.ControlForm(data=data, full_df=self.full_df)
        return form

    def get_table(self):
        """Return the summary table as an html string."""
        return self.__summary_table.to_html()

    def get_plot(self):
        """Return the plotly plot as an html string."""
        if self.__granularity == "Daily":
            fig = px.line(self.__summary_table, x="date", y="cost", color="name")
        elif self.__granularity == "Monthly":
            fig = px.line(self.__summary_table, x="month", y="cost", color="name")
        else:
            fig = px.bar(self.__summary_table, x="name", y="cost", color="name")
        return fig.to_html()

    @property
    def granularity(self):
        """Return the granularity."""
        return self.__granularity

    @property
    def class_param(self):
        """Return the class parameter."""
        return self.__class_param
